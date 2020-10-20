#Looking at average deployment performance by event area  
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

for(num_events in 1:n_events) 
{
  #Load data 
  setwd(paste0("../", num_events, " Events"))
  
  df <- read_csv(paste0(num_events,"events.csv"))
  df$Event <- as_factor(df$Event)
  dflookup <- read_csv(paste0(num_events,"events_locations.csv"))
  head(df)
  head(dflookup)
  
  df <- merge(df, dflookup, by = "RunId")
  head(df)
  
  small_immediate_start <- filter(df, EventStart == 0 & Required == 500)
  medium_immediate_start <- filter(df, EventStart == 0 & Required == 2000)
  large_immediate_start <- filter(df, EventStart == 0 & Required == 5000)  
  
  for(event_size in c("small","medium","large")) 
  {
    if(event_size == "large") 
    {df <- large_immediate_start 
    print("Visualising Large Event")
    psu_count <- 200}
    if(event_size == "medium") 
    {df <- medium_immediate_start
    print("Visualising Medium Event")
    psu_count <- 80}
    if(event_size == "small") 
    {df <- small_immediate_start
    print("Visualising Small Event")
    psu_count <- 20}
    
    #make event location a factor 
    df$EventLocations <- as_factor(df$EventLocations)
    #count how many levels it has - this is how many simulations have been run 
    simulation_count <- length(levels(df$EventLocations))
    
    #drop irrelavant vars
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
    
    
    #MMake Time a factor for ease of plotting clustered bar charts 
    df_average_deployment$Time <- as_factor(df_average_deployment$Time)
    
    #Divide the data up for grid of plots (HACKY)
    df_average_deployment_1 <- df_average_deployment[1:42,]
    df_average_deployment_2 <- df_average_deployment[43:81,]
    df_average_deployment_3 <- df_average_deployment[82:120,]
    
    
    #Now make three plots - clustered bar charts with error bars
    #---------------------------------------------------------------------------------------------------------------
    
    p1 <- ggplot(data=df_average_deployment_1, aes(x=Event, y=mean, fill=Time)) +
      geom_bar(stat="identity", position=position_dodge()) +
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
    
    p2 <- ggplot(data=df_average_deployment_2, aes(x=Event, y=mean, fill=Time)) +
      geom_bar(stat="identity", position=position_dodge()) +
      geom_errorbar(aes(ymin=mean-sd, ymax=mean+sd), width=.2,position=position_dodge(.9)) +
      theme(axis.text.x=element_text(angle=45,hjust=1)) +
      geom_hline(yintercept=10, linetype="dashed", color = "blue") +
      geom_hline(yintercept=40, linetype="dashed", color = "blue") +
      geom_hline(yintercept=60, linetype="dashed", color = "blue") +
      geom_hline(yintercept=100, linetype="dashed", color = "blue") +
      labs(y = "Mean % Deployed")  +
      theme(axis.title.x=element_blank())
    
    p3 <- ggplot(data=df_average_deployment_3, aes(x=Event, y=mean, fill=Time)) +
      geom_bar(stat="identity", position=position_dodge()) +
      geom_errorbar(aes(ymin=mean-sd, ymax=mean+sd), width=.2,position=position_dodge(.9)) +
      theme(axis.text.x=element_text(angle=45,hjust=1)) +
      geom_hline(yintercept=10, linetype="dashed", color = "blue") +
      geom_hline(yintercept=40, linetype="dashed", color = "blue") +
      geom_hline(yintercept=60, linetype="dashed", color = "blue") +
      geom_hline(yintercept=100, linetype="dashed", color = "blue") +
      labs(y = "Mean % Deployed")  +
      theme(axis.title.x=element_blank()) +
      labs(caption = "(based on data from ...)")
    
    
    #grid.arrange(p1,p2,p3)
    pdf(paste0("Mean_SD_deployment_",num_events,"_", event_size, "_events.pdf"), height = 11, width = 11)
    grid.arrange(p1,p2,p3)
    dev.off()
  }
}


# SIMPLE BAR CHART IMPLEMENTATION
# p1 <- ggplot(data=df_average_deployment_1, aes(x=Event, y=value_mean_DeployedPct, fill=Time)) +
#   geom_bar(stat="identity", position=position_dodge()) +
#   theme(axis.text.x=element_text(angle=45,hjust=1)) +
#   geom_hline(yintercept=10, linetype="dashed", color = "blue") +
#   geom_hline(yintercept=40, linetype="dashed", color = "blue") +
#   geom_hline(yintercept=60, linetype="dashed", color = "blue") +
#   labs(title = "Average deployment % by Event Location by 1,4,8 hour Mobilisation Targets",
#        subtitle = paste("Simulating",num_events,event_size, "sized simultaneous seats -",psu_count,"PSUs each - ALL COMBINATIONS of" ,num_events, "seats -", simulation_count , "simulations"),
#        y = "Mean % Deployed")  +
#   theme(axis.title.x=element_blank())
# 
# p2 <- ggplot(data=df_average_deployment_2, aes(x=Event, y=value_mean_DeployedPct, fill=Time)) +
#   geom_bar(stat="identity", position=position_dodge()) +
#   theme(axis.text.x=element_text(angle=45,hjust=1)) +
#   geom_hline(yintercept=10, linetype="dashed", color = "blue") +
#   geom_hline(yintercept=40, linetype="dashed", color = "blue") +
#   geom_hline(yintercept=60, linetype="dashed", color = "blue") +
#   labs(y = "Mean % Deployed")  +
#   theme(axis.title.x=element_blank())
# 
# p3 <- ggplot(data=df_average_deployment_3, aes(x=Event, y=value_mean_DeployedPct, fill=Time)) +
#   geom_bar(stat="identity", position=position_dodge()) +
#   theme(axis.text.x=element_text(angle=45,hjust=1)) +
#   geom_hline(yintercept=10, linetype="dashed", color = "blue") +
#   geom_hline(yintercept=40, linetype="dashed", color = "blue") +
#   geom_hline(yintercept=60, linetype="dashed", color = "blue") +
#   labs(y = "Mean % Deployed")  +
#   theme(axis.title.x=element_blank()) +
#   labs(caption = "(based on data from ...)")
# 
# #and put them togther 
# 
# 
# grid.arrange(p1,p2,p3)
# 
# pdf(paste0("Average_deployment_",num_events,"_", event_size, "_events.pdf"), height = 11, width = 11)
# grid.arrange(p1,p2,p3)
# dev.off()