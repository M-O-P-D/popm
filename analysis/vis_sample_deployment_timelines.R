library(tidyverse)
library(gridExtra)
library(rstudioapi)  

#REMEMBER TO SET YOUR WORKING DIRECTORY 
root_path_results <- getwd()
setwd(root_path_results)

#USER PARAM
n_events <- 3
shift_allocation <- 100
large_event_PSUs <- 99
medium_event_PSUs <- 35
small_event_PSUs <- 15

for(num_events in 1:n_events) 
{
  #Load data 
  setwd(paste0(root_path_results, "/", num_events, "events"))
  
  df <- read_csv(paste0(num_events,"events.csv"))
  df$Event <- as_factor(df$Event)
  dflookup <- read_csv(paste0(num_events,"events_locations.csv"))
  head(df)
  head(dflookup)
  
  df <- merge(df, dflookup, by = "RunId")
  head(df)
  
  small_immediate_start <- filter(df, EventStart == 0 & Required == (small_event_PSUs * 25))
  medium_immediate_start <- filter(df, EventStart == 0 & Required == (medium_event_PSUs * 25))
  large_immediate_start <- filter(df, EventStart == 0 & Required == (large_event_PSUs * 25))
  
  #store var for number of rows that need to be extracted to generate 12 sample plots 
  sample_count_rows <- num_events*12*24 #number of events x 12 plots x 24 hours 
  
  large_immediate_start_sample <- large_immediate_start[1:sample_count_rows,]
  medium_immediate_start_sample <- medium_immediate_start[1:sample_count_rows,]
  small_immediate_start_sample <- small_immediate_start[1:sample_count_rows,]
  tail(small_immediate_start_sample)
  
  #With lookup for event id string
  head(large_immediate_start_sample)
  
  p1 <- ggplot(data = large_immediate_start_sample, aes(x=Time, y=DeployedPct)) +
    xlim("1", "2", "3", "4", "5", "6","7", "8", "9","10", "11", "12","13", "14", "15","16", "17", "18","19", "20", "21", "22", "23") +
    geom_line(aes(color = Event)) + 
    #geom_point(size = 2, aes(color = as.factor(Event), shape = as.factor(Event))) +
    geom_segment(size=2, aes(x = 1, y = 0, xend = 1, yend = 10), color="grey") +
    geom_segment(size=2, aes(x = 4, y = 0, xend = 4, yend = 40), color="grey") +
    geom_segment(size=2, aes(x = 8, y = 0, xend = 8, yend = 60), color="grey") +
    labs(title = paste("Sample of" , num_events , "simultaneous large (", large_event_PSUs , "PSUs) seats-of-unrest scenarios"),
         subtitle = "Color Lines: % of required resources deployed to event, Vertical Bars: Recognised mobilisation targets",
         y = "% of required resources", x = "Hours from event start")+ 
    scale_fill_brewer(palette="Dark2") +
    facet_wrap(~ EventLocations , ncol=2)
  
  
  p2 <- ggplot(data = medium_immediate_start_sample, aes(x=Time, y=DeployedPct)) +
    xlim("1", "2", "3", "4", "5", "6","7", "8", "9","10", "11", "12","13", "14", "15","16", "17", "18","19", "20", "21", "22", "23") +
    geom_line(aes(color = Event)) + 
    #geom_point(size = 2, aes(color = as.factor(Event), shape = as.factor(Event))) +
    geom_segment(size=2, aes(x = 1, y = 0, xend = 1, yend = 10), color="grey") +
    geom_segment(size=2, aes(x = 4, y = 0, xend = 4, yend = 40), color="grey") +
    geom_segment(size=2, aes(x = 8, y = 0, xend = 8, yend = 60), color="grey") +
    labs(title = paste("Sample of" , num_events , "simultaneous medium (", medium_event_PSUs , "PSUs) seats-of-unrest scenarios"),
         subtitle = "Color Lines: % of required resources deployed to event, Vertical Bars: Recognised mobilisation targets",
         y = "% of required resources", x = "Hours from event start")+ 
    scale_fill_brewer(palette="Dark2") +
    facet_wrap(~ EventLocations , ncol=2)
  
  p3 <- ggplot(data = small_immediate_start_sample, aes(x=Time, y=DeployedPct)) +
    xlim("1", "2", "3", "4", "5", "6","7", "8", "9","10", "11", "12","13", "14", "15","16", "17", "18","19", "20", "21", "22", "23") +
    geom_line(aes(color = Event)) +
    #geom_point(size = 2, aes(color = as.factor(Event), shape = as.factor(Event))) +
    geom_segment(size=2, aes(x = 1, y = 0, xend = 1, yend = 10), color="grey") +
    geom_segment(size=2, aes(x = 4, y = 0, xend = 4, yend = 40), color="grey") +
    geom_segment(size=2, aes(x = 8, y = 0, xend = 8, yend = 60), color="grey") +
    labs(title = paste("Sample of" , num_events , "simultaneous small (", small_event_PSUs , "PSUs) seats-of-unrest scenarios"),
         subtitle = "Color Lines: % of required resources deployed to event, Vertical Bars: Recognised mobilisation targets",
         y = "% of required resources", x = "Hours from event start", fill = "Dose (mg)")+ 
    facet_wrap(~ EventLocations , ncol=2)
  
  
  pdf(paste0("Sample_deployment_timelines_",num_events,"_med-large_events.pdf"), height = 11, width = 11)
  grid.arrange(p1,p2)
  dev.off()
  
  pdf(paste0("Sample_deployment_timelines_",num_events,"_small-medium_events.pdf"), height = 11, width = 11)
  grid.arrange(p2,p3)
  dev.off()
}
