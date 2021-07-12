library(sf) 
library(tidyverse)
library(classInt) 
library(viridis)
library(ggrepel)

setwd("~/Dev/popm")
sf_gb <- st_read("data/force_boundaries_ugc.geojson", quiet = TRUE) #load in the force boundaries


nEvents <- 19
sizeEvents <- "small" 
deployPCT <- 100


mean_results <- read_csv("results/mean_dep_times.csv")              #import mean times 
sd_results <- read_csv("results/stddev_dep_times.csv")              #import sd times 

#join to spatial object 
sf_results <- left_join(sf_gb, mean_results, by = c("PFA16NM" = "Event"))
sf_results <- left_join(sf_results, sd_results, by = c("PFA16NM" = "Event"))

#trying to combine beds_cambs_hearts 
#all_minus_beds_cambs_hearts
beds_cambs_hearts <- st_combine(x = sf_gb[c(23,26,27),])


#Calculate Coefficient of variation - 
sf_results$CV <- sf_results$dep100.y / sf_results$dep100.x
#round it for visualisation on map 
sf_results$CVrnd <- round(sf_results$CV,2)


#sf_results$LABEL <- paste0(sf_results$PFA16NM,"\n", round(sf_results$dep100.x,2), "hr (" , round(sf_results$dep100.y,2), ")") # make a label from the name of the force and the rounded SD
sf_results$LABEL <- paste0(sf_results$PFA16NM,"\n", round(sf_results$dep100.x,2), "hr (" , sf_results$CVrnd, ")") # make a label from the name of the force and the rounded SD



p <- ggplot() +                                                                     # initialise a ggplot object
  geom_sf(data = sf_results,                                                        # add a simple features (sf) object
          aes(fill = cut_interval(dep100.x, 4)),                                    # group mean into equal intervals 
          alpha = 0.8,                                                              # add transparency to the fill
          colour = 'white',                                                         # make polygon boundaries white
          size = 0.3) +                                                             # adjust width of polygon boundaries
  #geom_sf_label(aes(label = NAME)) +
  scale_fill_brewer(palette = "OrRd",                                               # add palette
                    name = "Mean time from ideal") +                                # add legend title
  
  geom_label_repel(data = sf_results                                                # add the new labels and make sure they don't overlap  
            ,aes(x = LONG, y = LAT, label = LABEL)
            ,family = 'Avenir',   size=2.5) +

  labs(x = NULL, y = NULL,                                                          # drop axis titles
       title = "Mean & Coefficient of Variation - Latency in hours from Optimal Deployment",              # add title
       subtitle = paste0(nEvents, " ", sizeEvents, " event scenarios - ",deployPCT,"% deployment"),                     # add subtitle
       caption = "Contains OS data © Crown copyright and database right (2021)") +
  theme(panel.background = element_blank(), line = element_blank(), axis.text = element_blank(), axis.title = element_blank()) +
  coord_sf(datum = NA)

p
ggsave(p, filename = paste0(nEvents,sizeEvents,"_", deployPCT,"PCT.png"),  width = 30, height = 30, units = "cm")
