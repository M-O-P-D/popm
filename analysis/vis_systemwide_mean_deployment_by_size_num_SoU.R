#----------------------------------------------------------------------------------------------------------------------
#Look at overall performance 
#- i.e. plot number of events, and average resourcing met per event - facet by event size
#------------------------------------------------------------------
library(tidyverse)
library(gridExtra)
library(ggforce)
library(directlabels)

#REMEMBER TO SET YOUR WORKING DIRECTORY 
root_path_results <- getwd()
setwd(root_path_results)

#USER PARAM
n_events <- 3
shift_allocation <- 100
large_event_PSUs <- 99
medium_event_PSUs <- 35
small_event_PSUs <- 15


results <- data.frame(EventSize=factor(), 
                       NumEvents=integer(),
                       MeanAllocation_at_24hr=double(),
                       sdAllocation_at_24hr=double(),
                       stringsAsFactors=FALSE) 


#Step through all model conditions - numbers of SoU
for(num_events in 1:n_events) 
{

  #Load data 
  setwd(paste0(root_path_results, "/", num_events, "events"))
  raw <- read_csv(paste0(num_events,"events.csv"))
  raw$Event <- as_factor(raw$Event)
  
  #Step through all model conditions - size of SoU
  for(event_size in c("small","medium","large")) 
  {

    print(paste("Generating outcomes for", num_events, event_size, "events" ))
    
    #Subset data based on Param - pull only immediate events of right size - only extract allocation at hour 23
    if(event_size == "small") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == (small_event_PSUs * 25))}
    if(event_size == "medium") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == (medium_event_PSUs * 25))}
    if(event_size == "large") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == (large_event_PSUs * 25))}
    
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
  xlim(1, 10) +
  scale_x_continuous(breaks=c(1:10)) +
  labs(title = paste0("Allocation Trends by size and number of seats-of-unrest scenarios - ", shift_allocation, "% Shift Configuration"),
       subtitle = "Coloured Lines: Mean % of required resources allocated at event across all simulations.",
       y = "Mean % allocation at each seat of unrest across all simulations", x = "Number of simultaneous events",
       caption = "For scenarios with 1,2 & 3 events all unique combinations of events are simulated\nFor scenarios with 4 or more events a sample of 10,000 unique combinations is simulated")

pdf(paste0("../AggregateOut/Mean_Allocation_by_size_number_events.pdf"), height = 6, width = 11)
p1
dev.off()


#Do the same again but calculate outcomes per police force area
results <- data.frame(PFA=factor(),
                      MeanAllocation_at_24hr=double(),
                      sdAllocation_at_24hr=double(),
                      EventSize=factor(), 
                      NumEvents=integer(),
                      stringsAsFactors=TRUE
                      ) 

#Step through all model conditions - numbers of SoU
for(num_events in 1:n_events) 
{
  
  #Load data 
  setwd(paste0(root_path_results, "/", num_events, "events"))
  raw <- read_csv(paste0(num_events,"events.csv"))
  raw$Event <- as_factor(raw$Event)
  
  #Step through all model conditions - size of SoU
  for(event_size in c("small","medium","large")) 
  {
    
    print(paste("Generating outcomes for", num_events, event_size, "events" ))
    
    #Sbset data based on Param - pull only immediate events of right size - only extract allocation at hour 23
    if(event_size == "small") {df <- filter(raw, EventStart == 0 & Time == 23 & (small_event_PSUs * 25))}
    if(event_size == "medium") {df <- filter(raw, EventStart == 0 & Time == 23 & (medium_event_PSUs * 25))}
    if(event_size == "large") {df <- filter(raw, EventStart == 0 & Time == 23 & (large_event_PSUs * 25))}
    
    #drop everything apart from RunId, Event and AllocatedPCT
    df <- df[,c('RunId','Event','AllocatedPct')]
    #then group by RunId and get the mean allocation at 24hrs - 
    df <- df %>% 
      group_by(Event) %>% 
      summarise(
        mean = mean(AllocatedPct),
        sd = sd(AllocatedPct)) 
    
    df$EventSize <- event_size
    df$NumEvents <- num_events
    
    #and write the result into the results table
    results <- rbind(results, df)
  }
}

head(results)
results$EventSize <- as_factor(results$EventSize)


#Now Plot Results in pagniated facet wrap  

pdf(paste0("../AggregateOut/Mean_Allocation_by_size_number_events_facet_PFA.pdf"), height = 11, width = 18)

for (i in 1:5) {
print(ggplot(data = results, aes(x=NumEvents, y=mean)) +
  geom_line(aes(color = EventSize), size = 1.5) + 
  ylim(0, 100) +
  xlim(1, 10) +
  scale_x_continuous(breaks=c(1:10)) +
  labs(title = paste0("Allocation Trends by size and number of seats-of-unrest scenarios - ", shift_allocation, "% Shift Configuration"),
       subtitle = "Coloured Lines: Mean % of required resources allocated at event across all simulations.",
       y = "Mean % allocation at each seat of unrest across all simulations", x = "Number of simultaneous events",
       caption = "For scenarios with 1,2 & 3 events all unique combinations of events are simulated\nFor scenarios with 4 or more events a sample of 10,000 unique combinations is simulated") +
  facet_wrap_paginate(~Event, ncol = 3, nrow = 3, page = i))
}
dev.off() 





#subset just results for large SoU and graph all PFAs on one figure
results_large <- filter(results, EventSize == "large")
results_medium <- filter(results, EventSize == "medium")
results_small <- filter(results, EventSize == "small")


pdf(paste0("../AggregateOut/Mean_Allocation_by_size_number_events_combined_PFA.pdf"), height = 6, width = 11)

print(ggplot(data = results_large, aes(x=NumEvents, y=mean)) +
  geom_line(aes(color = Event), size = 1.5) + 
  ylim(0, 100) +
  xlim(1, 10) +
  scale_x_continuous(breaks=c(1:10)) +
  labs(title = paste0("Allocation Trends - Large seats-of-unrest scenarios - ", shift_allocation, "% Shift Configuration"),
       subtitle = "Coloured Lines: Mean % of required resources allocated at event across all simulations.",
       y = "Mean % allocation at each seat of unrest across all simulations", x = "Number of simultaneous events",
       caption = "For scenarios with 1,2 & 3 events all unique combinations of events are simulated\nFor scenarios with 4 or more events a sample of 10,000 unique combinations is simulated"))


print(ggplot(data = results_medium, aes(x=NumEvents, y=mean)) +
        geom_line(aes(color = Event), size = 1.5) + 
        ylim(0, 100) +
        xlim(1, 10) +
        scale_x_continuous(breaks=c(1:10)) +
        labs(title = paste0("Allocation Trends - Medium seats-of-unrest scenarios - ", shift_allocation, "% Shift Configuration"),
             subtitle = "Coloured Lines: Mean % of required resources allocated at event across all simulations.",
             y = "Mean % allocation at each seat of unrest across all simulations", x = "Number of simultaneous events",
             caption = "For scenarios with 1,2 & 3 events all unique combinations of events are simulated\nFor scenarios with 4 or more events a sample of 10,000 unique combinations is simulated"))


print(ggplot(data = results_small, aes(x=NumEvents, y=mean)) +
        geom_line(aes(color = Event), size = 1.5) + 
        ylim(0, 100) +
        xlim(1, 10) +
        scale_x_continuous(breaks=c(1:10)) +
        labs(title = paste0("Allocation Trends - Small seats-of-unrest scenarios - ", shift_allocation, "% Shift Configuration"),
             subtitle = "Coloured Lines: Mean % of required resources allocated at event across all simulations.",
             y = "Mean % allocation at each seat of unrest across all simulations", x = "Number of simultaneous events",
             caption = "For scenarios with 1,2 & 3 events all unique combinations of events are simulated\nFor scenarios with 4 or more events a sample of 10,000 unique combinations is simulated"))



dev.off()

#write out main results
write.csv2(results, file = "../AggregateOut/Mean_Allocations_by_PFA_by_size_count_SoU.csv")
