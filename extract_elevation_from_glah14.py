def extract_elevation_from_glah14(in_file_name, out_format='csv', long_min=0.0, long_max=360.0, lat_min=-90.0, lat_max=90.0):
    """snippet to convert GLAS/ICESat L2 Global Land Surface Altimetry Data (HDF5) to .csv or .shp format
    
    GLAS/ICEsat L2 Global Land Surface Altimetry Data (HDF5): https://nsidc.org/data/glah14
    GLAH14 Product Data Dictionary: https://nsidc.org/data/docs/daac/glas_altimetry/data-dictionary-glah14.html

    Arguments:
        in_file_name {String} -- [input file name]
    
    Keyword Arguments:
        out_format {str} -- the format of the output, can be 'csv' or 'shp' (default: {'csv'})
        long_min {float} -- minimum longitude of the area of interest (default: {0.0})
        long_max {float} -- maximum longitude of the area of interest (default: {360.0})
        lat_min {float} -- minimum latitude of the area of interest (default: {-90.0})
        lat_max {float} -- maximum latitude of the area of interest (default: {90.0})

    Note: The longitude in the original GLAH14 Product ranges between (0, 360). In the output file, the range of the longitude are converted to (-180, 180), with values greater than 180 represented using negative values.
    """
    import pandas as pd
    from shapely.geometry import Point
    import h5py
    from datetime import datetime, timedelta

    with h5py.File(in_file_name, mode='r') as f:
        index = f['/Data_40HZ/Time/i_rec_ndx'][:]
        timestamp = f['/Data_40HZ/DS_UTCTime_40'][:]
        
        latvar = f['/Data_40HZ/Geolocation/d_lat']
        latitude = latvar[:]

        lonvar = f['/Data_40HZ/Geolocation/d_lon']
        longitude = lonvar[:]

        elevar = f['/Data_40HZ/Elevation_Surfaces/d_elev']
        elev = elevar[:]
        elev_min, elev_max = int(elevar.attrs['valid_min']), int(elevar.attrs['valid_max'])
        
        sat_ele_corr_var = f['/Data_40HZ/Elevation_Corrections/d_satElevCorr']
        sat_ele_corr = sat_ele_corr_var[:]
        sat_ele_corr_min, sat_ele_corr_max = int(sat_ele_corr_var.attrs['valid_min']), int(sat_ele_corr_var.attrs['valid_max'])

        ele_bias_corr_var = f['/Data_40HZ/Elevation_Corrections/d_ElevBiasCorr']
        ele_bias_corr = ele_bias_corr_var[:]
        ele_bias_corr_min, ele_bias_corr_max = int(ele_bias_corr_var.attrs['valid_min']), int(ele_bias_corr_var.attrs['valid_max'])
        ele_bias_corr[ele_bias_corr < ele_bias_corr_min] = 0.0
        ele_bias_corr[ele_bias_corr > ele_bias_corr_max] = 0.0
        
        sat_corr_flag = f['/Data_40HZ/Quality/sat_corr_flg'][:]
        
        elev_use_flag = f['/Data_40HZ/Quality/elev_use_flg'][:]
        
        geoid = f['/Data_40HZ/Geophysical/d_gdHt'][:]

        srtmvar = f['/Data_40HZ/Geophysical/d_DEM_elv']
        srtm = srtmvar[:]
        srtm_min, srtm_max = int(srtmvar.attrs['valid_min']), int(srtmvar.attrs['valid_max'])
        
        columns=['RecordNumber', 'Timestamp', 'Latitude', 'Longitude', 
                    'Elevation', 'Sat_ele_corr', 'Ele_bias_corr', 'Sat_corr_flag',
                    'Elev_use_flag', 'Geoid', 'SRTM']
        df = pd.DataFrame(dict(zip(columns, [index, timestamp, latitude, longitude, elev, sat_ele_corr, 
                                                ele_bias_corr, sat_corr_flag, elev_use_flag, geoid, srtm])))
        
        df = df[(df['Latitude']<lat_max) & (df['Latitude']>lat_min)
            & (df['Longitude']<long_max) & (df['Longitude']>long_min) 
            & (df['Elevation']<elev_max) & (df['Elevation']>elev_min)
        & (df['SRTM']<srtm_max) & (df['SRTM']>srtm_min)
            & (df['Sat_corr_flag']==2) & (df['Elev_use_flag']==0)]

        df['Timestamp'] = base + pd.to_timedelta(df['Timestamp'], unit='s')
        df['Timestamp'] = df['Timestamp'].values.astype('datetime64[s]')
        df['Date'] = df['Timestamp'].dt.strftime('%Y/%m/%d')
        df['Time'] = df['Timestamp'].dt.time.values.astype(str) #converting the time to string otherwise Geopandas will raise error when exporting as .shp
        
        df.loc[df['Longitude'] > 180, 'Longitude'] -= 360.0
        
        df['Elevation_corrected'] = df['Elevation'] + df['Sat_ele_corr'] + df['Ele_bias_corr'] - df['Geoid'] - 0.7
        df = df[['RecordNumber', 'Date', 'Time', 'Latitude', 'Longitude', 'Elevation_corrected', 'SRTM']]
        
        if out_format == 'csv':
            df.to_csv(in_file_name.rsplit('.')[0] + '.csv')
        else:
            geometry = [Point(xy) for xy in zip(df['Longitude'], df['Latitude'])]
            df = df.drop(['Longitude', 'Latitude'], axis=1)
            crs = {'init': 'epsg:4326'}
            gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
            gdf.to_file(driver = 'ESRI Shapefile', filename= in_file_name.rsplit('.')[0] + '.shp')