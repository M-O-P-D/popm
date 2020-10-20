#----------------------------------------------------------------------------------------------------------------------
#Look at overall performance 
#- i.e. plot number of events, and average resourcing met per event - facet by event size
#------------------------------------------------------------------
library(dplyr)
library(ggplot2)
library(readr)
library(tidyverse)
library(gridExtra)
library(reshape2)
library(rstudioapi)  

#USER PARAM
n_events <- 10

results <- data.frame(EventSize=factor(), 
                       NumEvents=integer(),
                       MeanAllocation_at_24hr=double(),
                       sdAllocation_at_24hr=double(),
                       stringsAsFactors=FALSE) 

for(num_events in 1:n_events) 
{

  #Load data 
  setwd(paste0("../", num_events, " Events"))
  raw <- read_csv(paste0(num_events,"events.csv"))
  raw$Event <- as_factor(raw$Event)
  
  #Set USER PARAM
  for(event_size in c("small","medium","large")) 
  {

    print(paste("Generating outcomes for", num_events, event_size, "events" ))
    
    #Sbset data based on Param - pull only immediate events of right size - only extract allocation at hour 23
    if(event_size == "small") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == 500)}
    if(event_size == "medium") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == 2000)}
    if(event_size == "large") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == 5000)}
    
    head(df)
    
    #drop everything apart from RunId and AllocatedPCT
    df <- df[,c('RunId','AllocatedPct')]
    #then group by RunId and get the mean allocation at 24hrs - 
    df <- df %>% 
      group_by(RunId) %>% 
      summarise(
        n = n(), 
        mean = mean(AllocatedPct))

    success_pct <- (mean(df$mean))
    sd = (sd(df$mean))
    #and write the result into the results table
    results <- rbind(results, data.frame(EventSize = event_size, NumEvents = num_events, MeanAllocation_at_24hr = success_pct, sdAllocation_at_24hr = sd))
  }
}


#Now Plot Results 

p1 <- ggplot(data = results, aes(x=NumEvents, y=MeanAllocation_at_24hr)) +
  geom_line(aes(color = EventSize), size = 1.5) + 
  ylim(0, 100) +
  #geom_point(size = 2, aes(color = as.factor(Event), shape = as.factor(Event))) +
  labs(title = paste("Allocation Trends by size and number of seats-of-unrest scenarios"),
       subtitle = "Coloured Lines: Mean % of required resources allocated at event across all simulations.",
       y = "Mean % Allocation at 24hrs", x = "Number of simultaneous events",
       caption = paste("\n\nGenerating Script:", print(rstudioapi::getActiveDocumentContext()$path))) +
  annotate("text", x = 3, y = 7, label = "For scenarios with 1,2 & 3 events all unique combinations of events are simulated.\nFor scenarios with 4 or more events a sample of 10,000 unique combinations is simulated")

pdf(paste0("../Mean_Allocation_by_size_number_events.pdf"), height = 6, width = 11)
p1
dev.off()