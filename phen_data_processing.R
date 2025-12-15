# Script to processs vegetation synchrony data 

# Load libraries ----
pacman::p_load(tidyverse, ggplot2,
               sf, terra, lubridate,
               rnaturalearth)

# Get mapping data 
country_pols <- ne_countries(scale = "large", type = "countries")
bounds <- ne_states(country = c("Canada", "United States of America"))
Lakes <- ne_download(scale = 110, type = "lakes", category = "physical")

# Path to local data repository 
path <- "C:/Users/Jelan/OneDrive/Desktop/University/University of Guelph/Lab_projects/Synchrony_of_migration/local_data/"

# Load movement database 
maco <- read_csv(paste0(path, "maco_data_analysis_10_2025.csv"))

# load phenology data extracted from the "MODIS/061/MCD12Q2" database on GEE
phen <- read_csv(paste0(path, "Modis_land_cover_dynamics100.csv"))

# Identify the points for which we have no phenology data and map them  
miss <- maco %>% filter(!(id.row %in% unique(phen$id))) %>%
  filter(year >= 2001)

# Individual/points for which penology data could not be collected can normally be explained by:
# Missing coordinates
# Missing timing values (arr.br, dep.br, arr.nbr, dep.nbr) or NA in "year" column
# Data collected before 2001 or after 2025

ggplot(data = country_pols)+
  geom_sf(colour = NA, fill = "lightgray") +
  coord_sf(xlim = c(-160, 160),ylim = c(-55, 70), expand = F) + 
  geom_point(data = miss, mapping = aes(x = lon.br, y = lat.br), pch = 21, fill = "coral1", colour = "white")+
  theme_bw()

ggplot(data = country_pols)+
  geom_sf(colour = NA, fill = "lightgray") +
  coord_sf(xlim = c(-160, 160),ylim = c(-55, 70), expand = F) + 
  geom_point(data = miss, mapping = aes(x = lon.nbr1, y = lat.nbr1), pch = 21, fill = "blue", colour = "white")+
  theme_bw()


# Identify the points for which we have no phenology data and map them  
miss <- maco %>% filter(!(id.row %in% unique(phen$id))) %>%
  filter(year >= 2001)

# Add dates to the phenology dataset that are based on the numbers provided in the MODIS dataset 
# These numbers are in the format : number of days since 01-01-1970
phen <- phen %>% rowwise() %>%
  mutate(across(.cols = c('Greenup_1', 'MidGreenup_1','Peak_1',
                'Maturity_1',  'Senescence_1', 'MidGreendown_1', 'Dormancy_1',
                'Greenup_2', 'MidGreenup_2','Peak_2',
                'Maturity_2',  'Senescence_2', 'MidGreendown_2', 'Dormancy_2'),
         .fns = ~as.Date(.x, format = "%d/%m/%Y"),
      .names = "{.col}_dt"
    ))

# To see the units for the ther columns EIVI minimum, amplitute, and area, see 
# page 7 of the user's guide https://lpdaac.usgs.gov/documents/1417/MCD12Q2_User_Guide_V61.pdf

# We merge the breeding site phenology data with the maco dataset 
dt_phen_br <- maco %>% merge(phen[phen$location == "br.arrival", c('id','Greenup_1_dt','Peak_1_dt',  'Senescence_1_dt',
                                                                        'Greenup_1','Peak_1', 'Senescence_1')],
                          by.x = "id.row", by.y = "id") %>%
# Let's take a sample of this dataset for plotting
  filter(!duplicated(id.study))

# try plotting green_up times on a map.
# We can label them with the actual value for the green_up time, and cross-reference it with the 
# "MODIS/061/MCD12Q2" database usign the inspector tool on the gee website 
ggplot(data = bounds)+
  geom_sf(colour = "black", fill = "lightgray") +
  coord_sf(xlim = c(-86, -70),ylim = c(40, 48), expand = F) + 
  geom_point(data = dt_phen_br, mapping = aes(x = lon.br, y = lat.br, fill = yday(Greenup_1_dt)), pch = 21, colour = "white")+
  scale_fill_continuous(name = "Greenup day")+
  geom_text(data = dt_phen_br, mapping = aes(x = lon.br, y = lat.br, label = paste0(Greenup_1_dt,"(",Greenup_1,")")), nudge_x = 0.2, nudge_y = - 0.2 , size = 4)+
  theme_bw()

# Now let's have a look at nonbreeding sites missing green up information 
dt_phen_nbr <- maco %>% merge(phen[phen$location == "nbr.arrival", c('id','Greenup_1_dt','Peak_1_dt',  'Senescence_1_dt',
                                                                                  'Greenup_1','Peak_1', 'Senescence_1')],
                                            by.x = "id.row", by.y = "id") 

dt_phen_nbr_na <- dt_phen_nbr %>% filter(is.na(Greenup_1_dt))

# let's map these sites 

ggplot(data = country_pols)+
  geom_sf(colour = NA, fill = "lightgray") +
  coord_sf(xlim = c(-160, 160),ylim = c(-55, 70), expand = F) + 
  geom_point(data = dt_phen_nbr_na, mapping = aes(x = lon.nbr1, y = lat.nbr1), pch = 21, fill = "blue", colour = "white")+
  theme_bw()
