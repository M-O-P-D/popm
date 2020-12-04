#Looking at average deployment performance by event area  
#------------------------------------------------------------------
library(tidyverse)
library(gridExtra)
library(rstudioapi)  

#REMEMBER TO SET YOUR WORKING DIRECTORY 
root_path_results <- getwd()
setwd(root_path_results)

#USER PARAM
n_events <- 10
shift_allocation <- 100
large_event_PSUs <- 99
medium_event_PSUs <- 35
small_event_PSUs <- 15


pdf(paste0("AggregateOut/Mean_SD_deployment_by_events.pdf"), height = 11, width = 11)

for(event_size in c("small","medium","large")) 
{
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
  
    if(event_size == "large") 
    {df <- filter(df, EventStart == 0 & Required == (large_event_PSUs * 25))  
    print(paste0("Visualising ", num_events, " Large Events"))
    psu_count <- 200}
    if(event_size == "medium") 
    {df <- filter(df, EventStart == 0 & Required == (medium_event_PSUs * 25))
    print(paste0("Visualising ", num_events, "Medium Events"))
    psu_count <- 80}
    if(event_size == "small") 
    {df <- filter(df, EventStart == 0 & Required == (small_event_PSUs * 25))
    print(paste0("Visualising ", num_events, " Small Events"))
    psu_count <- 20}
    
    #make event location a factor 
    df$EventLocations <- as_factor(df$EventLocations)
    #count how many levels it has - this is how many simulations have been run 
    simulation_count <- length(levels(df$EventLocations))
    
    #drop irrelevant vars
    tmp <- df[,c(3,2,7)] 
    tmp
    
    #now extract deployment % at 1,4 and 8 hr KPIs
    tmp <- filter(tmp, Time == 1 | Time == 4 | Time == 8 )
    summary(tmp)
    tmp
    
    #Melt data from wide to long format groupong by EventLocation and take average of 1,4,8 hr deployment %s
    df_melt <- melt(tmp, id = c("Event", "Time"))
    #df_average_deployment <- dcast(df_melt, Event + Time ~ variable, aggregate=c(mean, sd))
    
    df_average_deployment <- df_melt %>% 
      group_by(Event,Time) %>% 
      summarise(
        mean = mean(value),
        sd = sd(value))
    
    
    #Make Time a factor for ease of plotting clustered bar charts 
    df_average_deployment$Time <- as_factor(df_average_deployment$Time)
    
    #ensure Event levels for df_average_deployment$Event are in alphabetical order and then order by Event- for consistency in plotting order
    df_average_deployment$Event <- factor(as.character(df_average_deployment$Event))
    df_average_deployment <- df_average_deployment %>% arrange(Event)
      
    
    #Divide the data up for grid of plots (HACKY)
    df_average_deployment_1 <- df_average_deployment[1:42,] 
    df_average_deployment_2 <- df_average_deployment[43:81,] 
    df_average_deployment_3 <- df_average_deployment[82:120,] 
    
    
    #Now make three plots - clustered bar charts with error bars
    #---------------------------------------------------------------------------------------------------------------
    
    p1 <- ggplot(data=df_average_deployment_1, aes(x=Event , y=mean, fill=Time)) +
      geom_bar(stat="identity", position=position_dodge()) +
      ylim(0, 120) +
      geom_errorbar(aes(ymin=mean-sd, ymax=mean+sd), width=.2,position=position_dodge(.9)) +
      theme(axis.text.x=element_text(angle=45,hjust=1)) +
      geom_hline(yintercept=10, linetype="dashed", color = "blue") +
      geom_hline(yintercept=40, linetype="dashed", color = "blue") +
      geom_hline(yintercept=60, linetype="dashed", color = "blue") +
      geom_hline(yintercept=100, linetype="dashed", color = "blue") +
      labs(title = "Mean & SD of deployment % by Event Location by 1,4,8 hour Mobilisation Targets",
           subtitle = paste("Simulating",num_events,event_size, "sized simultaneous seats -",psu_count,"PSUs each - ALL COMBINATIONS of" ,num_events, "seats -", simulation_count , "simulations"),
           y = "Mean % Deployed")  +
      theme(axis.title.x=element_blank())
    
    p2 <- ggplot(data=df_average_deployment_2, aes(x=Event , y=mean, fill=Time)) +
      geom_bar(stat="identity", position=position_dodge()) +
      ylim(0, 120) +
      geom_errorbar(aes(ymin=mean-sd, ymax=mean+sd), width=.2,position=position_dodge(.9)) +
      theme(axis.text.x=element_text(angle=45,hjust=1)) +
      geom_hline(yintercept=10, linetype="dashed", color = "blue") +
      geom_hline(yintercept=40, linetype="dashed", color = "blue") +
      geom_hline(yintercept=60, linetype="dashed", color = "blue") +
      geom_hline(yintercept=100, linetype="dashed", color = "blue") +
      labs(y = "Mean % Deployed")  +
      theme(axis.title.x=element_blank())
    
    p3 <- ggplot(data=df_average_deployment_3, aes(x=Event , y=mean, fill=Time)) +
      geom_bar(stat="identity", position=position_dodge()) +
      ylim(0, 120) +
      geom_errorbar(aes(ymin=mean-sd, ymax=mean+sd), width=.2,position=position_dodge(.9)) +
      theme(axis.text.x=element_text(angle=45,hjust=1)) +
      geom_hline(yintercept=10, linetype="dashed", color = "blue") +
      geom_hline(yintercept=40, linetype="dashed", color = "blue") +
      geom_hline(yintercept=60, linetype="dashed", color = "blue") +
      geom_hline(yintercept=100, linetype="dashed", color = "blue") +
      labs(y = "Mean % Deployed")  +
      theme(axis.title.x=element_blank()) +
      labs(caption = "(based on data from ...)")
    
    print(grid.arrange(p1,p2,p3))
    
  }
}
dev.off()

