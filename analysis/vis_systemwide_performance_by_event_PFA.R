#----------------------------------------------------------------------------------------------------------------------
#Look at overall performance - BOX PLOTS
#- Boxplots represent % of Required Allocation at each simulated event in police force area  
#----------------------------------------------------------------------------------------------------------------------
library(tidyverse)
library(gridExtra)
library(rstudioapi)  

#REMEMBER TO SET YOUR WORKING DIRECTORY 
root_path_results <- getwd()
setwd(root_path_results)

#USER PARAM
n_events <- 10
shift_allocation <- 100

results <- data.frame(Event=factor(),
                       AllocatedPct=double(),
                       NumEvents=integer(),
                       EventSize=factor(), 
                       stringsAsFactors=FALSE) 

for(num_events in 1:n_events) 
{

  #Load data 
  setwd(paste0(root_path_results, "/", num_events, "events"))
  raw <- read_csv(paste0(num_events,"events.csv"))
  raw$Event <- as_factor(raw$Event)
  
  head(raw)
  
  #Set USER PARAM
  for(event_size in c("small","medium","large")) 
  {
    print(paste("Generating outcomes for", num_events, event_size, "events" ))
    
    #Subset data based on Param - pull only immediate events of right size - only extract allocation at hour 23
    if(event_size == "small") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == 500)}
    if(event_size == "medium") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == 2000)}
    if(event_size == "large") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == 5000)}
    
    #drop everything apart from RunId and AllocatedPCT
    df <- df[,c('Event','AllocatedPct')]
    
    df$num_events = num_events
    df$event_size = event_size
    
    results <- rbind(results, df)
  }
}

p1 <- ggplot(results, aes(x=factor(num_events), y=AllocatedPct, fill=factor(event_size))) + 
  geom_boxplot(outlier.shape = NA) +
  labs(title = paste("Allocation Trends by size and number of seats-of-unrest scenarios"),
       subtitle = "Boxplots represent % of Required Allocation at each simulated event in police force area. 1 to 3 events all combinations 4+ Events - sample of 10000 combinations .",
       y = "% of Required Allocation at Event", x = "Number of simultaneous events") +
  facet_wrap(~Event)


pdf(paste0("../AggregateOut/XBoxplots_by_PFA_size_number_events.pdf"), height = 11, width = 18)
p1
dev.off()
