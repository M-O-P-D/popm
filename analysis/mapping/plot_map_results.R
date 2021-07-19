library(sf) 
library(tidyverse)
library(classInt) 
library(viridis)
library(ggrepel)
library(qdap)
library(janitor)
library(lubridate)

options(pillar.sigfig = 10)
options(digits = 10)

setwd("~/Dev/popm")
sf_gb <- st_read("data/forces.json", quiet = TRUE) #load in the force boundaries

#generate LAT and LONG Cols from label_anchor
sf_gb$latlong <- genXtract(sf_gb$label_anchor, "(", ")")
sf_gb$LAT <- as.numeric(substr(sf_gb$latlong,1,17))
sf_gb$LONG <- as.numeric(substr(sf_gb$latlong,18,35))

#specify what to map
nEvents <- 7
sizeEvents <- "small" 


#100% Deployment -----------------------------------------------------------------------------------------
deployPCT <- 100

#import mean / sd times for specified experiment 
results <- read_csv(paste0("results/new/",nEvents,"-", sizeEvents, "_summary.csv")) %>% clean_names()   

#join to spatial object 
sf_results <- left_join(sf_gb, results, by = c("name" = "location"))

#replace NAs with 0 (when Stddev = 0 (1 event configs))
sf_results <- sf_results %>%
  mutate_at(vars(stddev_0_1,  stddev_0_4, stddev_0_6,   stddev_1_0), ~replace_na(., 0))



#Calculate Coefficient of variation - 
sf_results$CV <- sf_results$stddev_1_0 / sf_results$mean_1_0

#remove NaNs (if mean is zero - divide by zero above) and replace with 0
sf_results <- sf_results %>% mutate_at(vars(CV), ~replace(., is.nan(.), 0))

#round it for visualisation on map 
sf_results$CVrnd <- round(sf_results$CV,2) 

#build a string for labels that converts mean decimal hours to hours / minutes 
sf_results$mean_1_0_STR <- paste0(floor(sf_results$mean_1_0) , "hr " , round(
    ((sf_results$mean_1_0 - floor(sf_results$mean_1_0)) * 60)
    ,0), "min") 

#sf_results$LABEL <- paste0(sf_results$PFA16NM,"\n", round(sf_results$dep100.x,2), "hr (" , round(sf_results$dep100.y,2), ")") # make a label from the name of the force and the rounded SD
sf_results$LABEL <- paste0(sf_results$name,"\n", sf_results$mean_1_0_STR, " (" , sf_results$CVrnd, ")") # make a label from the name of the force and the rounded SD


p <- ggplot() +                                                                     # initialise a ggplot object
  geom_sf(data = sf_results,                                                        # add a simple features (sf) object
          aes(fill = cut_width(mean_1_0, width = 1, center = 0.5)),              # group mean into equal intervals of 1hr
          alpha = 0.8,                                                              # add transparency to the fill
          colour = 'white',                                                         # make polygon boundaries white
          size = 0.3) +                                                             # adjust width of polygon boundaries
  #geom_sf_label(aes(label = NAME)) +
  scale_fill_brewer(palette = "OrRd",                                               # add palette
                    name = "Average Hours from \nOptimal Deployment") +             # add legend title
  
  geom_label_repel(data = sf_results                                                # add the new labels and make sure they don't overlap  
            ,aes(x = LAT, y = LONG, label = LABEL)
            ,family = 'Avenir',   size=2.5) +

  labs(x = NULL, y = NULL,                                                                                # drop axis titles
       title = paste0("Average Hours to " ,deployPCT, "% Deployment (Coefficient of Variation)"),           # add title
       subtitle = paste0(nEvents, " ", sizeEvents, " event scenarios - ",deployPCT,"% deployment"),       # add subtitle
       caption = "Contains OS data © Crown copyright and database right (2021)") +                        # add copyright
  theme(panel.background = element_blank(), line = element_blank(), axis.text = element_blank(), axis.title = element_blank()) +
  coord_sf(datum = NA)

#plot it
p 
#save it
ggsave(p, filename = paste0("results/new/",nEvents,sizeEvents,"_", deployPCT,"PCT.png"),  width = 30, height = 30, units = "cm")


#60% Deployment -----------------------------------------------------------------------------------------
deployPCT <- 60

#import mean / sd times for specified experiment 
results <- read_csv(paste0("results/",nEvents,"-", sizeEvents, "_summary.csv")) %>% clean_names()   

#join to spatial object 
sf_results <- left_join(sf_gb, results, by = c("name" = "location"))

#replace NAs with 0 (when Stddev = 0 (1 event configs))
sf_results <- sf_results %>%
  mutate_at(vars(stddev_0_1, stddev_0_4, stddev_0_6, stddev_1_0), ~replace_na(., 0))

#Calculate Coefficient of variation - 
sf_results$CV <- sf_results$stddev_0_6 / sf_results$mean_0_6

#remove NaNs (if mean is zero - divide by zero above) and replace with 0
sf_results <- sf_results %>% mutate_at(vars(CV), ~replace(., is.nan(.), 0))

#round it for visualisation on map 
sf_results$CVrnd <- round(sf_results$CV,2) 

#build a string for labels that converts mean decimal hours to hours / minutes 
sf_results$mean_0_6_STR <- paste0(floor(sf_results$mean_0_6) , "hr " , round(
  ((sf_results$mean_0_6 - floor(sf_results$mean_0_6)) * 60)
  ,0), "min") 

#sf_results$LABEL <- paste0(sf_results$PFA16NM,"\n", round(sf_results$dep60.x,2), "hr (" , round(sf_results$dep60.y,2), ")") # make a label from the name of the force and the rounded SD
sf_results$LABEL <- paste0(sf_results$name,"\n", sf_results$mean_0_6_STR, " (" , sf_results$CVrnd, ")") # make a label from the name of the force and the rounded SD


p <- ggplot() +                                                                     # initialise a ggplot object
  geom_sf(data = sf_results,                                                        # add a simple features (sf) object
          aes(fill = cut_width(mean_0_6, width = 1, center = 0.5)),              # group mean into equal intervals of 1hr
          alpha = 0.8,                                                              # add transparency to the fill
          colour = 'white',                                                         # make polygon boundaries white
          size = 0.3) +                                                             # adjust width of polygon boundaries
  #geom_sf_label(aes(label = NAME)) +
  scale_fill_brewer(palette = "OrRd",                                               # add palette
                    name = "Average Hours from \nOptimal Deployment") +             # add legend title
  
  geom_label_repel(data = sf_results                                                # add the new labels and make sure they don't overlap  
                   ,aes(x = LAT, y = LONG, label = LABEL)
                   ,family = 'Avenir',   size=2.5) +
  
  labs(x = NULL, y = NULL,                                                                                # drop axis titles
       title = paste0("Average Hours to " ,deployPCT, "% Deployment (Coefficient of Variation)"),          # add title
       subtitle = paste0(nEvents, " ", sizeEvents, " event scenarios - ",deployPCT,"% deployment"),       # add subtitle
       caption = "Contains OS data © Crown copyright and database right (2021)") +                        # add copyright
  theme(panel.background = element_blank(), line = element_blank(), axis.text = element_blank(), axis.title = element_blank()) +
  coord_sf(datum = NA)

#plot it
p 
#save it
ggsave(p, filename = paste0("results/new/",nEvents,sizeEvents,"_", deployPCT,"PCT.png"),  width = 30, height = 30, units = "cm")




#40% Deployment -----------------------------------------------------------------------------------------
deployPCT <- 40

#import mean / sd times for specified experiment 
results <- read_csv(paste0("results/",nEvents,"-", sizeEvents, "_summary.csv")) %>% clean_names()   

#join to spatial object 
sf_results <- left_join(sf_gb, results, by = c("name" = "location"))

#replace NAs with 0 (when Stddev = 0 (1 event configs))
sf_results <- sf_results %>%
  mutate_at(vars(stddev_0_1, stddev_0_4, stddev_0_6, stddev_1_0), ~replace_na(., 0))

#Calculate Coefficient of variation - 
sf_results$CV <- sf_results$stddev_0_4 / sf_results$mean_0_4

#remove NaNs (if mean is zero - divide by zero above) and replace with 0
sf_results <- sf_results %>% mutate_at(vars(CV), ~replace(., is.nan(.), 0))

#round it for visualisation on map 
sf_results$CVrnd <- round(sf_results$CV,2) 

#build a string for labels that converts mean decimal hours to hours / minutes 
sf_results$mean_0_4_STR <- paste0(floor(sf_results$mean_0_4) , "hr " , round(
  ((sf_results$mean_0_4 - floor(sf_results$mean_0_4)) * 60)
  ,0), "min") 

#sf_results$LABEL <- paste0(sf_results$PFA16NM,"\n", round(sf_results$dep40.x,2), "hr (" , round(sf_results$dep40.y,2), ")") # make a label from the name of the force and the rounded SD
sf_results$LABEL <- paste0(sf_results$name,"\n", sf_results$mean_0_4_STR, " (" , sf_results$CVrnd, ")") # make a label from the name of the force and the rounded SD


p <- ggplot() +                                                                     # initialise a ggplot object
  geom_sf(data = sf_results,                                                        # add a simple features (sf) object
          aes(fill = cut_width(mean_0_4, width = 1, center = 0.5)),              # group mean into equal intervals of 1hr
          alpha = 0.8,                                                              # add transparency to the fill
          colour = 'white',                                                         # make polygon boundaries white
          size = 0.3) +                                                             # adjust width of polygon boundaries
  #geom_sf_label(aes(label = NAME)) +
  scale_fill_brewer(palette = "OrRd",                                               # add palette
                    name = "Average Hours from \nOptimal Deployment") +             # add legend title
  
  geom_label_repel(data = sf_results                                                # add the new labels and make sure they don't overlap  
                   ,aes(x = LAT, y = LONG, label = LABEL)
                   ,family = 'Avenir',   size=2.5) +
  
  labs(x = NULL, y = NULL,                                                                                # drop axis titles
       title = paste0("Average Hours to " ,deployPCT, "% Deployment (Coefficient of Variation)"),             # add title
       subtitle = paste0(nEvents, " ", sizeEvents, " event scenarios - ",deployPCT,"% deployment"),       # add subtitle
       caption = "Contains OS data © Crown copyright and database right (2021)") +                        # add copyright
  theme(panel.background = element_blank(), line = element_blank(), axis.text = element_blank(), axis.title = element_blank()) +
  coord_sf(datum = NA)

#plot it
p 
#save it
ggsave(p, filename = paste0("results/new/",nEvents,sizeEvents,"_", deployPCT,"PCT.png"),  width = 30, height = 30, units = "cm")


#10% Deployment -----------------------------------------------------------------------------------------
deployPCT <- 10

#import mean / sd times for specified experiment 
results <- read_csv(paste0("results/",nEvents,"-", sizeEvents, "_summary.csv")) %>% clean_names()   

#join to spatial object 
sf_results <- left_join(sf_gb, results, by = c("name" = "event"))

#replace NAs with 0 (when Stddev = 0 (1 event configs))
sf_results <- sf_results %>%
  mutate_at(vars(stddev_0_1, stddev_0_4, stddev_0_6, stddev_1_0), ~replace_na(., 0))

#Calculate Coefficient of variation - 
sf_results$CV <- sf_results$stddev_0_1 / sf_results$mean_0_1

#remove NaNs (if mean is zero - divide by zero above) and replace with 0
sf_results <- sf_results %>% mutate_at(vars(CV), ~replace(., is.nan(.), 0))

#round it for visualisation on map 
sf_results$CVrnd <- round(sf_results$CV,2) 

#build a string for labels that converts mean decimal hours to hours / minutes 
sf_results$mean_0_1_STR <- paste0(floor(sf_results$mean_0_1) , "hr " , round(
  ((sf_results$mean_0_1 - floor(sf_results$mean_0_1)) * 60)
  ,0), "min") 

#sf_results$LABEL <- paste0(sf_results$PFA16NM,"\n", round(sf_results$dep10.x,2), "hr (" , round(sf_results$dep10.y,2), ")") # make a label from the name of the force and the rounded SD
sf_results$LABEL <- paste0(sf_results$name,"\n", sf_results$mean_0_1_STR, " (" , sf_results$CVrnd, ")") # make a label from the name of the force and the rounded SD


p <- ggplot() +                                                                     # initialise a ggplot object
  geom_sf(data = sf_results,                                                        # add a simple features (sf) object
          aes(fill = cut_width(mean_0_1, width = 1, center = 0.5)),              # group mean into equal intervals of 1hr
          alpha = 0.8,                                                              # add transparency to the fill
          colour = 'white',                                                         # make polygon boundaries white
          size = 0.3) +                                                             # adjust width of polygon boundaries
  #geom_sf_label(aes(label = NAME)) +
  scale_fill_brewer(palette = "OrRd",                                               # add palette
                    name = "Average Hours from \nOptimal Deployment") +             # add legend title
  
  geom_label_repel(data = sf_results                                                # add the new labels and make sure they don't overlap  
                   ,aes(x = LAT, y = LONG, label = LABEL)
                   ,family = 'Avenir',   size=2.5) +
  
  labs(x = NULL, y = NULL,                                                                                # drop axis titles
       title = paste0("Average Hours to " ,deployPCT, "% Deployment (Coefficient of Variation)"),              # add title
       subtitle = paste0(nEvents, " ", sizeEvents, " event scenarios - ",deployPCT,"% deployment"),       # add subtitle
       caption = "Contains OS data © Crown copyright and database right (2021)") +                        # add copyright
  theme(panel.background = element_blank(), line = element_blank(), axis.text = element_blank(), axis.title = element_blank()) +
  coord_sf(datum = NA)

#plot it
p 
#save it
ggsave(p, filename = paste0("results/new/",nEvents,sizeEvents,"_", deployPCT,"PCT.png"),  width = 30, height = 30, units = "cm")


