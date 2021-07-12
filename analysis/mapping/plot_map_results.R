library(sf) 
library(tidyverse)
library(classInt) 
library(viridis)

setwd("~/Dev/popm")
sf_gb <- st_read("data/force_boundaries_ugc.geojson", quiet = TRUE)

glimpse(sf_gb)
st_geometry(sf_gb)
plot(st_geometry(sf_gb))
