#----------------------------------------------------------------------------------------------------------------------
#Look at overall performance 
#- i.e. plot number of events, and percentage of scenarios fully resourced - facet by event size
#------------------------------------------------------------------
library(tidyverse)
library(gridExtra)


#REMEMBER TO SET YOUR WORKING DIRECTORY 
root_path_results <- getwd()
setwd(root_path_results)

#USER PARAM
n_events <- 10
shift_allocation <- 100

#create an empty DF to store results 
results <- data.frame(EventSize=factor(), 
                      NumEvents=integer(),
                      SuccessPct=double(), 
                      stringsAsFactors=FALSE) 

for(num_events in 1:n_events) 
{

  #Load data 
  setwd(paste0(root_path_results, "/", num_events, "events"))
  raw <- read_csv(paste0(num_events,"events.csv"))
  raw$Event <- as_factor(raw$Event)
  
  #Set USER PARAM
  for(event_size in c("small","medium","large")) 
  {
    print(paste("Generating overall efficiency outcomes for", num_events, event_size, "events" ))
    
    #Sbset data based on Param - pull only immediate events of right size - only extract allocation at hour 23
    if(event_size == "small") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == 500)}
    if(event_size == "medium") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == 2000)}
    if(event_size == "large") {df <- filter(raw, EventStart == 0 & Time == 23 & Required == 5000)}
    
    head(df)
    
    #drop everything apart from RunId and AllocatedPCT
    df <- df[,c('RunId','AllocatedPct')]
    #then group by RunId and get the lowest value - 
    df <- df %>% group_by(RunId) %>% summarise(mean = min(AllocatedPct))
    #if it's less than 100 - in that model the PFAs failed to respond with all required resources - flag as 0 otherwise 1
    df$Success <- ifelse(df$mean <100, 0, 1)
    #finally calculate the % of simulations that were successfully resourced 
    success_pct <- (sum(df$Success) / nrow(df)) * 100
    #and write the result into the results table
    results <- rbind(results, data.frame(EventSize = event_size, NumEvents = num_events, SuccessPct = success_pct))
    
  }
}

#Now Plot Results 

p1 <- ggplot(data = results, aes(x=NumEvents, y=SuccessPct)) +
  geom_line(aes(color = EventSize), size = 1.5) + 
  ylim(0, 100) +
  #geom_point(size = 2, aes(color = as.factor(Event), shape = as.factor(Event))) +
  labs(title = paste("Overall efficiency by size and number of seats-of-unrest scenarios"),
       subtitle = "Coloured Lines: % of simulation runs in which all events were successfully resourced.",
       y = "% of simulations fully resourced", x = "Number of simultaneous events",
       caption = paste("\n\nGenerating Script:")) +
  annotate("text", x = 5.5, y = 15, label = "For scenarios with 1,2 & 3 events all unique combinations of events are simulated.\nFor scenarios with 4 or more events a sample of 10,000 unique combinations is simulated")

pdf(paste0("../AggregateOut/Overall_efficiency_by_size_number_events.pdf"), height = 11, width = 11)
p1
dev.off()
