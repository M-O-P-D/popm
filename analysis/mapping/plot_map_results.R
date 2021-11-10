#------------------------------------------------------------------------------------------------
#PRODUCE BLANK PLOTS FOR REPORT?

library(sf) 
library(tidyverse)
library(classInt) 
library(viridis)
library(ggrepel)
library(qdap)
library(janitor)
library(lubridate)
library(languageserver)
library(viridis)           

options(pillar.sigfig = 10)
options(digits = 10)

#boolean to turn on or off generating plots - in case you just want to produce output tables 
generate_plots = FALSE 

setwd("~/Dev/popm")
sf_gb <- st_read("data/forces.json") #load in the force boundaries
#alliances <- st_read("data/alliances.geojson")

#generate LAT and LONG Cols from label_anchor
sf_gb$latlong <- genXtract(sf_gb$label_anchor, "(", ")")
sf_gb$LAT <- as.numeric(substr(sf_gb$latlong,1,17))
sf_gb$LONG <- as.numeric(substr(sf_gb$latlong,18,35))

#specify location of result files 
folder <- "weight-amount-travel-mobilisation"

#specify what combination of event size and number you want to plot at what deployment level
nEvents <- 19
sizeEvents <- "small" 
deployPCT <- 60

#or create a dataframe containing all experimental combos to step through at all deployment levels
d <- data.frame(size = c('large', 'medium', 'small'),
                ex1n = c(1, 3, 7), 
                ex1n = c(2, 6, 13), 
                ex1n = c(3, 8, 19)
                )

#OPTION 1: Plotting with adaptive pallete - more variation per map - but red in map A is not the same value as red in map B 
#main loop - skip to center if analysing a specific combination 
for(i in 1:3)
{
  sizeEvents <- d[i,1] 
  for(j in 2:4)
  {
    
    #create a structure to store results for 10,40,60,100% deployments in each of 9 configs to include in report 
    results_for_report_table <- sf_gb %>% select(name) #first grab force names
    results_for_report_table <- st_set_geometry(results_for_report_table, NULL) #then drop spatial info
    
    nEvents <- d[i,j]
    for(deployPCT in c(10,40,60,100))
    {
      print(paste("Analysing" ,deployPCT ,"% deployment - ", nEvents, sizeEvents, "events" ))

      #import mean / sd times for specified experiment 
      results <- read_csv(paste0("results/", folder, "/",nEvents,"-", sizeEvents, "_summary.csv")) %>% clean_names()   
      #results <- read_csv(paste0("results/", folder, "/19-small_summary.csv")) %>% clean_names()   
      
      #join to spatial object 
      sf_results <- left_join(sf_gb, results, by = c("name" = "location"))
      
      #replace NAs with 0 (when Stddev = 0 (1 event configs))
      sf_results <- sf_results %>%
        mutate_at(vars(stddev_0_1,  stddev_0_4, stddev_0_6,   stddev_1_0), ~replace_na(., 0))
      
      #condition on deployPCT to automate selection of relevant mean and sd
      if (deployPCT == 10) { 
        sf_results <- rename(sf_results, stddev = stddev_0_1) 
        sf_results <- rename(sf_results, mean = mean_0_1)
      }
      if (deployPCT == 40) { 
        sf_results <- rename(sf_results, stddev = stddev_0_4) 
        sf_results <- rename(sf_results, mean = mean_0_4)
      }
      if (deployPCT == 60) { 
        sf_results <- rename(sf_results, stddev = stddev_0_6) 
        sf_results <- rename(sf_results, mean = mean_0_6)
      }
      if (deployPCT == 100) { 
        sf_results <- rename(sf_results, stddev = stddev_1_0) 
        sf_results <- rename(sf_results, mean = mean_1_0)
      }
      
      
      #Calculate Coefficient of variation - 
      sf_results$CV <- sf_results$stddev / sf_results$mean
      
      #remove NaNs (if mean is zero - divide by zero above) and replace with 0
      sf_results <- sf_results %>% mutate_at(vars(CV), ~replace(., is.nan(.), 0))
      
      #round it for visualisation on map 
      sf_results$CVrnd <- round(sf_results$CV,2) 
      
      #build a string for labels that converts mean decimal hours to hours / minutes 
      sf_results$mean_STR <- paste0(floor(sf_results$mean) , "hr " , round(
        ((sf_results$mean - floor(sf_results$mean)) * 60)
        ,0), "min") 
      
      #sf_results$LABEL <- paste0(sf_results$PFA16NM,"\n", round(sf_results$dep100.x,2), "hr (" , round(sf_results$dep100.y,2), ")") # make a label from the name of the force and the rounded SD
      sf_results$LABEL <- paste0(sf_results$name,"\n", sf_results$mean_STR, " (" , sf_results$CVrnd, ")") # make a label from the name of the force and the rounded SD
      sf_results$forTable <- paste0(sf_results$mean_STR, " (" , sf_results$CVrnd, ")") # make a label from the name of the force and the rounded SD
      
      #quickly write out 100% deployment results for table in paper
      tableout <- sf_results %>% select(name,forTable)
      #drop the sf geometry 
      tableout <- st_set_geometry(tableout, NULL)
      
      # then left join this % deployment results to results_for_report_table
      results_for_report_table <- left_join(results_for_report_table, tableout, by = c("name" = "name"))
      
      
      #write_csv(x = tableout, paste0("results/", folder, "/",nEvents,sizeEvents,"_", deployPCT,"PCT.csv"))
      
      #check if we need to generate plots 
        if (generate_plots == TRUE) 
        {
        p <- ggplot() +                                                                     # initialise a ggplot object
          geom_sf(data = sf_results,                                                        # add a simple features (sf) object
                  aes(fill = cut_width(mean, width = 1, center = 0.5)),                   # group mean into equal intervals of 1hr
                  #aes(fill = mean_1_0), 
                  alpha = 0.8,                                                              # add transparency to the fill
                  colour = 'white',                                                         # make polygon boundaries white
                  size = 0.3) +                                                             # adjust width of polygon boundaries
        
            
          scale_fill_brewer(palette = "OrRd",                                               # add palette - in case of more than 9 vals scale_fill_manual(values = getPalette(colourCount),     
                            name = paste0("Average Hours to \n",deployPCT ,"% Deployment"), # add legend title
                            drop = TRUE) +
          
          geom_label_repel(data = sf_results                                                # add the new labels and make sure they don't overlap  
                           ,aes(x = LAT, y = LONG, label = LABEL)
                           ,family = 'Avenir',   size=3) +
          
          labs(x = NULL, y = NULL) +                                                                               # drop axis titles
               #title = paste0("Average Hours to " ,deployPCT, "% Deployment (Coefficient of Variation)"),         # add title
               #subtitle = paste0(nEvents, " ", sizeEvents, " event scenarios - ",deployPCT,"% deployment"),       # add subtitle
               #caption = "Contains OS data © Crown copyright and database right (2021)") +                        # add copyright
          theme(panel.background = element_blank(), line = element_blank(), axis.text = element_blank(), axis.title = element_blank()) +
          coord_sf(datum = NA)
  
          #or plot it without legend 
          #p <- p + theme(legend.position = "none") 
          p <- p + theme(legend.position = c(0.89, 0.8))
          p
          #save it
          ggsave(p, filename = paste0("results/", folder, "/REPORT_",nEvents,sizeEvents,"_", deployPCT,"PCT.png"),  width = 20, height = 30, units = "cm")

      }
    }
    #now you've collected deployment numbers at 10,40,60,100% prepare results for report table 
    colnames(results_for_report_table) <- c("Police Force Area", "10% Deployment", "40% Deployment", "60% Deployment", "100% Deployment")
    #and write it out 
    write_csv(x = results_for_report_table, paste0("results/", folder, "/REPORT_",nEvents,sizeEvents,"_table.csv"))
  }
}




#SPECIAL CASE: FOR 19 SMALL EVENTS WE NEED A 10 COLOR PALLETTE 

#for extending pallette 
colourCount = 10
getPalette = colorRampPalette(brewer.pal(9, "OrRd"))

nEvents <- 19
sizeEvents <- "small" 
deployPCT <- 60


print(paste("SPECIAL Analysing" ,deployPCT ,"% deployment - ", nEvents, sizeEvents, "events" ))

#import mean / sd times for specified experiment 
results <- read_csv(paste0("results/", folder, "/",nEvents,"-", sizeEvents, "_summary.csv")) %>% clean_names()   

#join to spatial object 
sf_results <- left_join(sf_gb, results, by = c("name" = "location"))

#replace NAs with 0 (when Stddev = 0 (1 event configs))
sf_results <- sf_results %>%
  mutate_at(vars(stddev_0_1,  stddev_0_4, stddev_0_6,   stddev_1_0), ~replace_na(., 0))

#condition on deployPCT to automate selection of relevant mean and sd
if (deployPCT == 10) { 
  sf_results <- rename(sf_results, stddev = stddev_0_1) 
  sf_results <- rename(sf_results, mean = mean_0_1)
}
if (deployPCT == 40) { 
  sf_results <- rename(sf_results, stddev = stddev_0_4) 
  sf_results <- rename(sf_results, mean = mean_0_4)
}
if (deployPCT == 60) { 
  sf_results <- rename(sf_results, stddev = stddev_0_6) 
  sf_results <- rename(sf_results, mean = mean_0_6)
}
if (deployPCT == 100) { 
  sf_results <- rename(sf_results, stddev = stddev_1_0) 
  sf_results <- rename(sf_results, mean = mean_1_0)
}


#Calculate Coefficient of variation - 
sf_results$CV <- sf_results$stddev / sf_results$mean

#remove NaNs (if mean is zero - divide by zero above) and replace with 0
sf_results <- sf_results %>% mutate_at(vars(CV), ~replace(., is.nan(.), 0))

#round it for visualisation on map 
sf_results$CVrnd <- round(sf_results$CV,2) 

#build a string for labels that converts mean decimal hours to hours / minutes 
sf_results$mean_STR <- paste0(floor(sf_results$mean) , "hr " , round(
  ((sf_results$mean - floor(sf_results$mean)) * 60)
  ,0), "min") 

#sf_results$LABEL <- paste0(sf_results$PFA16NM,"\n", round(sf_results$dep100.x,2), "hr (" , round(sf_results$dep100.y,2), ")") # make a label from the name of the force and the rounded SD
sf_results$LABEL <- paste0(sf_results$name,"\n", sf_results$mean_STR, " (" , sf_results$CVrnd, ")") # make a label from the name of the force and the rounded SD
sf_results$forTable <- paste0(sf_results$mean_STR, " (" , sf_results$CVrnd, ")") # make a label from the name of the force and the rounded SD

#quickly write out 100% deployment results for table in paper
tableout <- sf_results %>% select(name,forTable)
write_csv(x = tableout, paste0("results/", folder, "/",nEvents,sizeEvents,"_", deployPCT,"PCT.csv"))


p <- ggplot() +                                                                     # initialise a ggplot object
  geom_sf(data = sf_results,                                                        # add a simple features (sf) object
          aes(fill = cut_width(mean, width = 1, center = 0.5)),                   # group mean into equal intervals of 1hr
          #aes(fill = mean_1_0), 
          alpha = 0.8,                                                              # add transparency to the fill
          colour = 'white',                                                         # make polygon boundaries white
          size = 0.3) +                                                             # adjust width of polygon boundaries
  
  
  scale_fill_manual(values = getPalette(colourCount),                                              # add palette - in case of more than 9 vals scale_fill_manual(values = getPalette(colourCount),     
                    name = paste0("Average Hours to \n",deployPCT ,"% Deployment"), # add legend title
                    drop = TRUE) +
  
  geom_label_repel(data = sf_results                                                # add the new labels and make sure they don't overlap  
                   ,aes(x = LAT, y = LONG, label = LABEL)
                   ,family = 'Avenir',   size=3) +
  
  labs(x = NULL, y = NULL) +                                                                               # drop axis titles
  #title = paste0("Average Hours to " ,deployPCT, "% Deployment (Coefficient of Variation)"),         # add title
  #subtitle = paste0(nEvents, " ", sizeEvents, " event scenarios - ",deployPCT,"% deployment"),       # add subtitle
  #caption = "Contains OS data © Crown copyright and database right (2021)") +                        # add copyright
  theme(panel.background = element_blank(), line = element_blank(), axis.text = element_blank(), axis.title = element_blank()) +
  coord_sf(datum = NA)

#or plot it without legend 
#p <- p + theme(legend.position = "none") 
p <- p + theme(legend.position = c(0.89, 0.8))
p
#save it
ggsave(p, filename = paste0("results/", folder, "/REPORT_",nEvents,sizeEvents,"_", deployPCT,"PCT.png"),  width = 20, height = 30, units = "cm")

