# Extraction of phenological variables From the 
# MODIS/Terra+Aqua Land Cover Dynamics Yearly L3 Global 500m SIN Grid V061
# dataset on the Google Earth Engine Catalog 

# Import the necessary libraries 
import ee # Earth Engine
import pandas as pd # equivalent of dplyr for Python 
from datetime import datetime, timedelta # to deal with dates 

# Authentication should be performed in the command line prompt
# ee.authenticate() will not work here, in the Rstudio script editor 
# Use the commands below in the command line prompt:
      # conda activate gee
      # earthengine authenticate 

# I have only needed to authenticate once on my laptop

# Initialize Google Earth Engine 
ee.Initialize()

# Helper function to extract values from specific bits in a bitmask -----
# This is to apply data quality filters 
def bitwise_extract(input, from_bit, to_bit):
    mask_size = ee.Number(1).add(to_bit).subtract(from_bit)
    mask = ee.Number(1).leftShift(mask_size).subtract(1)
    return input.rightShift(from_bit).bitwiseAnd(mask)

# Function to extract phenological data ----
def get_spat_data(gee_dataset, buffer_radius, fl_crt):
  
  ##############################################################################
  
  # Function parameters 
  
  # gee_dataset: name of the dataset from which the data will be extracted 
  # This dataset should always be "MODIS/061/MCD12Q2"
  
  # buffer_radius: Radius of the buffer around the locations used by birds,
  # within which we will calculate the median of phenological measurements 
  
  # fl_crt: Filtering criteria for the data analysis, should be a number between
  # 0 and 3. All pixels with a bit value less than or equal to this will be used
  # 0 is best quality and 3 is worst. 
  
  # E.g., if you set fl_crt to 1, then all pixel with a quality of 1 and 0 will be used 
  # If you set fl_crt to 2, then all pixel with a quality of 2, 1 and 0 will be used 
  
  # Uncomment these these lines to set parameters and test the function line-by-line
  # This is for troubleshooting only 
  # gee_dataset = "MODIS/061/MCD12Q2"
  # buffer_radius = 100000
  # fl_crt = 1
  
  ##############################################################################
  
  # Helper function to generate buffer point based on the buffer radius 
  def buffer_points(feature):
      pt = ee.Feature(feature)
      return pt.buffer(buffer_radius)
  
  # Load individual bird location data from CSV
  # add "_test" at the end of the filename to get the test database 
  track_data = pd.read_csv(r"C:/Users/Jelan/OneDrive/Desktop/University/University of Guelph/Lab_projects/Synchrony_of_migration/local_data/maco_data_analysis_10_2025.csv", encoding ="ISO-8859-1", dtype={"year": str})

  # Compute arrival/departure dates, as well as year start and end dates 
  track_data ["dep_br"] = pd.to_datetime(track_data["year"] + "-01-01") + pd.to_timedelta(track_data["doy.dep.br"], unit="D")
  track_data ["dep_br_yr_start"] = pd.to_datetime(track_data ["dep_br"].dt.strftime("%Y") + "-01-01") 
  track_data ["dep_br_yr_end"] = track_data ["dep_br_yr_start"] + pd.DateOffset(years= 1)
  
  track_data ["arr_nbr"] = pd.to_datetime(track_data["year"] + "-01-01") + pd.to_timedelta(track_data["doy.arr.nbr"], unit="D")
  track_data ["arr_nbr_yr_start"] = pd.to_datetime(track_data ["arr_nbr"].dt.strftime("%Y") + "-01-01") 
  track_data ["arr_nbr_yr_end"] = track_data ["arr_nbr_yr_start"] + pd.DateOffset(years= 1)
  
  track_data ["dep_nbr"] = pd.to_datetime(track_data["year"] + "-01-01") + pd.to_timedelta(track_data["doy.dep.nbr"], unit="D")
  track_data ["dep_nbr_yr_start"] = pd.to_datetime(track_data ["dep_nbr"].dt.strftime("%Y") + "-01-01") 
  track_data ["dep_nbr_yr_end"] = track_data ["dep_nbr_yr_start"] + pd.DateOffset(years= 1)
  
  track_data ["arr_br"] = pd.to_datetime(track_data["year"] + "-01-01") + pd.to_timedelta(track_data["doy.arr.br"], unit="D")
  track_data ["arr_br_yr_start"] = pd.to_datetime(track_data ["arr_br"].dt.strftime("%Y") + "-01-01") 
  track_data ["arr_br_yr_end"] = track_data ["arr_br_yr_start"] + pd.DateOffset(years= 1)
  
  # We only retain inidividuals with data collected within the time when the 
  # MCD12Q2.006dataset is available 
  # if the timings fall outside of the period covered by the dataset, the function will fail to run 
  track_data = track_data[(pd.to_numeric(track_data['year']) < 2025) & (pd.to_numeric(track_data['year']) >= 2001)]
  
  # Using the times above, we will prepare sets of points for which data will be extracted 

  # The lat, lon, and and migration timings are critical for the function to run
  # if the coords are NaN, the function will not run
  # As a result, we are going to create four separate dataset for arrival and 
  # departure sites that exclude any birds with missing data 
  
  track_data_arr_br = track_data.dropna(subset=["lat.br", "lon.br", "year", 
    "doy.arr.br", "arr_br"])
    
  track_data_dep_br = track_data.dropna(subset=["lat.br", "lon.br", "year", 
     "doy.dep.br", "dep_br"])

  track_data_arr_nbr = track_data.dropna(subset=["lat.nbr1", "lon.nbr1", "year", 
    "doy.arr.nbr", "arr_nbr"])
  
  track_data_dep_nbr = track_data.dropna(subset=["lon.nbr2", "lat.nbr2", "year", 
     "doy.dep.nbr", "dep_nbr"])

  # We are going to convert all rows in the datasetsets we have created to points
  # Then, we'll merge them into a single point dataset (a FeatureCollection in gee)
  # Some point are at the same location, but have a different timing attributes
  # that will be used to extract phenology data
  # (e.g., this is the case for all breeding site points). 
  
  # We start by converting the four datasets to lists of point features 
  
  # Conversion to features for the first nonbreeding site dataset
  nbr1_features = [ee.Feature(
          ee.Geometry.Point([row["lon.nbr1"], row["lat.nbr1"]]),
          {
              "id": int(row["id.row"]),
              "location": "nbr.arrival",
              "year_start": row["arr_nbr_yr_start"].isoformat(),
              "event_date":  row["arr_nbr"].isoformat(),
              "event_date_doy": int(row["doy.arr.nbr"]),
              "year_end": row["arr_nbr_yr_end"].isoformat(),
              "lon": row["lon.nbr1"],
              "lat": row["lat.nbr1"],
          },
      )
      for _, row in track_data_arr_nbr.iterrows()
      ]
        
  # Conversion to features for the second nonbreeding site dataset   
  nbr2_features = [ee.Feature(
            ee.Geometry.Point([row["lon.nbr2"], row["lat.nbr2"]]),
            {
                
                "id": int(row["id.row"]),
                "location": "nbr.departure",
                "year_start": row["dep_nbr_yr_start"].isoformat(),
                "event_date":  row["dep_nbr"].isoformat(),
                "event_date_doy": int(row["doy.dep.nbr"]),
                "year_end": row["dep_nbr_yr_end"].isoformat(),
                "lon": row["lon.nbr2"],
                "lat": row["lat.nbr2"],
                
            },
        )
        for _, row in track_data_dep_nbr.iterrows()
        ]
    
  # Conversion to features for the breeding site (at arrival)    
  br1_features = [ee.Feature(
            ee.Geometry.Point([row["lon.br"], row["lat.br"]]),
            {

                "id": int(row["id.row"]),
                "location": "br.departure",
                "year_start": row["dep_br_yr_start"].isoformat(),
                "event_date":  row["dep_br"].isoformat(),
                "event_date_doy": int(row["doy.dep.br"]),
                "year_end": row["dep_br_yr_end"].isoformat(),
                "lon": row["lon.br"],
                "lat": row["lat.br"],
             },
      )
      for _, row in track_data_dep_br.iterrows()
      ]   
      
   # Conversion to features for the breeding site (at departure)         
  br2_features = [ee.Feature(
            ee.Geometry.Point([row["lon.br"], row["lat.br"]]),
            {

                "id": int(row["id.row"]),
                "location": "br.arrival",
                "year_start": row["arr_br_yr_start"].isoformat(),
                "event_date":  row["arr_br"].isoformat(),
                "event_date_doy": int(row["doy.arr.br"]),
                "year_end": row["arr_br_yr_end"].isoformat(),
                "lon": row["lon.br"],
                "lat": row["lat.br"],
             },
      )
      for _, row in track_data_arr_br.iterrows()
      ]   
    
  # We merge the four lists of features and convert the output into a single a featurecollection 
  all_features = nbr1_features + nbr2_features + br1_features + br2_features
  pts = ee.FeatureCollection( all_features)
  
  # Create spatial buffers arround each of the points in the feature collection 
  pts_buff = pts.map(buffer_points)

  # Load the GEE dataset from which we will extract vegetation data 
  spatdat = ee.ImageCollection(gee_dataset)
  
  # Function to apply data quality bit masks
  # Here we use the filters from MCD12Q2.006
  def qc_filter(img, cycle):
      img_date = ee.Image(img).date()
      qc_img1 = ee.ImageCollection(spatdat).filterDate(img_date).first().select("QA_Detailed_1")
      qc_img2 = ee.ImageCollection(spatdat).filterDate(img_date).first().select("QA_Detailed_2")
  
  # Create bitmasks
  # See description of bitmasks here: https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD12Q2#bands
  # for each bit, we use a all values lower or equal to the flt_crt parameter
  
      # bit_mask for cycle 1 
      bit_masks1 = [
        # Bitmasks for QA_Detailed_1 
        bitwise_extract(qc_img1, 0, 1).lte(fl_crt),  
        bitwise_extract(qc_img1, 2,3).lte(fl_crt), 
        bitwise_extract(qc_img1, 4,5).lte(fl_crt),
        bitwise_extract(qc_img1, 6,7).lte(fl_crt), 
        bitwise_extract(qc_img1, 8,9).lte(fl_crt),  
        bitwise_extract(qc_img1, 10, 11).lte(fl_crt), 
        bitwise_extract(qc_img1, 12,13).lte(fl_crt), 
       ]
       
      # bit_mask for cycle 2 
      bit_masks2 = [
        #Bitmasks for QA_Detailed_2 
        bitwise_extract(qc_img2, 0, 1).lte(fl_crt),  
        bitwise_extract(qc_img2, 2,3).lte(fl_crt), 
        bitwise_extract(qc_img2, 4,5).lte(fl_crt),
        bitwise_extract(qc_img2, 6,7).lte(fl_crt), 
        bitwise_extract(qc_img2, 8,9).lte(fl_crt),  
        bitwise_extract(qc_img2, 10, 11).lte(fl_crt), 
        bitwise_extract(qc_img2, 12,13).lte(fl_crt), 
      ]
      
      # if cycle is 1, then use only the bits for that cycle and combine them into one mask 
      if cycle == 1:
        combined_mask = ee.Image(1)
        for mask in bit_masks1:
            combined_mask = combined_mask.And(mask)
            
      # if cycle is 2, then use only the bits for that cycle and combine them into one mask 
      elif  cycle == 2:
        combined_mask = ee.Image(1)
        for mask in bit_masks2:
            combined_mask = combined_mask.And(mask)
            
      return img.updateMask(combined_mask)
    
  # function that maps over bufferfeatures to extract vegetation data
  def process_feature(feat):
    
    # set the start and end time for the data extraction 
    start_date = ee.Date(feat.get("year_start"))
    end_date = ee.Date(feat.get("year_end"))
      
    # For each feature. we get a single image that corresponds to the year in which the arrival/departure occurred 
    img = spatdat.filterDate(start_date, end_date).first()
    
    # get bands from cycle 1 with the appropriate mask 
    img1 = qc_filter(img, cycle = 1).select('NumCycles', 'Greenup_1', 'MidGreenup_1','Peak_1',
    'Maturity_1',  'Senescence_1', 'MidGreendown_1', 'Dormancy_1',  'EVI_Minimum_1',
    'EVI_Amplitude_1', 'EVI_Area_1', 'QA_Overall_1', 'QA_Detailed_1')
    
    #get bands from the cycle 2 with the appropriate mask
    img2 = qc_filter(img, cycle = 2).select('Greenup_2', 'MidGreenup_2','Peak_2',
    'Maturity_2',  'Senescence_2', 'MidGreendown_2', 'Dormancy_2',  'EVI_Minimum_2',
    'EVI_Amplitude_2', 'EVI_Area_2', 'QA_Overall_2', 'QA_Detailed_2')
    
    # Applying a different mask to each cycle allows us to avoid loosing information if the masks conflict with each other. 

    # merge the two resulting images
    img = img1.addBands(img2)
      
    # Reduce the image (Note we are using the median of pixel values within the buffer - this should be changed if desired)
    reduced = img.reduceRegion(ee.Reducer.median(), feat.geometry(), scale =  500, maxPixels = 30000000)
    
    return feat.setMulti(reduced).set({"year": img.date().format()})
  
  # We apply our function to extrcact the data to the points 
  point_stats = pts_buff.map(process_feature)
  
  #return the points 
  return point_stats
    
    
# test calls to the get_spat_data function ----

# With 100 km buffer 
phenology100 = get_spat_data(
  gee_dataset = "MODIS/061/MCD12Q2",
  buffer_radius = 100000,
  fl_crt = 1
)

# Export to Google Drive 
task = ee.batch.Export.table.toDrive(
  collection = phenology100,
  description = "Modis_land_cover_dynamics100",
  folder = "GEE_imports",
  fileFormat = "CSV",
  selectors = ["id", "location", "year_start", "year_end", "event_date",
  "event_date_doy", "system:index", "lat", "lon",
  'NumCycles', 'Greenup_1', 'Greenup_2', 'MidGreenup_1', 'MidGreenup_2', 'Peak_1',
  'Peak_2', 'Maturity_1', 'Maturity_2', 'Senescence_1', 'Senescence_2',
  'MidGreendown_1', 'MidGreendown_2', 'Dormancy_1', 'Dormancy_2', 'EVI_Minimum_1',
  'EVI_Minimum_2', 'EVI_Amplitude_1','EVI_Amplitude_2', 'EVI_Area_1', 'EVI_Area_2',
  'QA_Overall_1', 'QA_Overall_2', 'QA_Detailed_1', 'QA_Detailed_2']
  )

# Start data export 
task.start()

# Check on task status
task.status()


