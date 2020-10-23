#----------------------------------------------------------------------------------------------------------------------
#Look at how resources are distributed 
#----------------------------------------------------------------------------------------------------------------------
library(dplyr)
library(ggplot2)
library(readr)
library(tidyverse)
library(gridExtra)
library(reshape2)
library(rstudioapi)  
library(ggforce)


n_events <- 10

for(num_events in 1:n_events) 
{

  #Load data 
  setwd(paste0("../", num_events, " Events"))
  df <- read_csv(paste0(num_events,"events_allocations.csv"))
  head(df)
  df <- df[,c('EventForce','AssignedForce', 'PSUs','Requirement')]
  df$proportion_req = df$PSUs/df$Requirement
  
  head(df)
  
  for(event_size in c("small","medium","large"))
  {
    #large events 
    if(event_size == "small") {df_cut <- filter(df, Requirement == 20)}
    if(event_size == "medium") {df_cut <- filter(df, Requirement == 80)}
    if(event_size == "large") {df_cut <- filter(df, Requirement == 200)}
    
    df_cut <- df_cut %>% 
      group_by(EventForce, AssignedForce) %>% 
      summarise(
        n = n(), 
        sum = sum(PSUs),
        mean = mean(PSUs),
        sd = sd(PSUs),
        mean_prop = mean(proportion_req),
        sd_prop = sd(proportion_req),
        )
    
    df_cut
    
    #First visualise top exporters
    ggplot(data = df_cut, aes(x=AssignedForce, y=mean)) +
      geom_bar(stat="identity", position=position_dodge()) + 
      #geom_errorbar(aes(ymin=mean-sd, ymax=mean+sd), width=.2,position=position_dodge(.9)) +
      theme(axis.text.x=element_text(angle=45,hjust=1, size=10)) +
      labs(title = paste("Top Exporters of PSUs"),
           subtitle = paste("Analsyses of" , num_events , "x" ,event_size, "SoU Scenarios"),
           y = "Mean number of PSUs sent to events",
           caption = paste("\n\nGenerating Script:", print(rstudioapi::getActiveDocumentContext()$path))) 
    
    ggsave(file = paste0("../Top_exporters_", num_events, "SoU.pdf"), height = 6, width = 11)
    
    
    #Then breakdown by Event Location - for events occuring in a particular PFA - from where do they typically get their PSUs
    for (i in 1:10)
    {
      ggplot(data = df_cut, aes(x=AssignedForce, y=mean_prop)) +
        geom_bar(stat="identity", position=position_dodge()) + 
        theme(axis.text.x=element_text(angle=45,hjust=1, size=8)) +
        labs(title = paste("Who gets what from where?"),
             subtitle = paste("Analsyses of PSU providers by Event Location - " , event_size, "x", num_events, " SoU Scenarios"),
             y = "Mean proportion of PSUs sent to events",
             x = "Provider of Resource",
             caption = paste("\n\nGenerating Script:", print(rstudioapi::getActiveDocumentContext()$path))) +
        facet_wrap_paginate(~EventForce, ncol = 2, nrow = 2, page = i)
      
      ggsave(file = paste0("../Who_gets_what_from_where_", event_size, "x", num_events, "SoU_p", i, ".pdf"), height = 6, width = 11)
    }  
  }
}



#----------------------------------------------------------------------------------------------------------------
#Do you get from your alliance or from elsewhere?
#----------------------------------------------------------------------------------------------------------------

n_events <- 10

for(num_events in 1:n_events) 
{
  setwd(paste0("../", num_events, " Events"))
  df <- read_csv(paste0(num_events,"events_allocations.csv"))
  head(df)
  
  df$proportion_req = df$PSUs/df$Requirement
  df
  
  
  for(event_size in c("small","medium","large"))
  {
    #large events 
    if(event_size == "small") {df_cut <- filter(df, Requirement == 20)}
    if(event_size == "medium") {df_cut <- filter(df, Requirement == 80)}
    if(event_size == "large") {df_cut <- filter(df, Requirement == 200)}
    
    df_cut
    
    #This sums across all simulations how many PSUs have been provided by self/alliance and how many from outside  
    df_cut_grouped <- df_cut %>% 
      group_by(EventForce, Alliance) %>% 
      summarise(
        sum_PSUs = sum(proportion_req)
      )
    
    #now work out the total number of PSUs supllied in general 
    df_cut_grouped2 <-     df_cut_grouped %>% 
      group_by(EventForce) %>% 
      summarise(
        total_PSUs = sum(sum_PSUs)
      )
    
    
    #Merge the two files - and calc what proportion of total PSUs recieved across all models come from alliance or otherwise.
    df_cut_grouped3 <- merge(df_cut_grouped, df_cut_grouped2, by = "EventForce")
    df_cut_grouped3$prop <- df_cut_grouped3$sum_PSUs/df_cut_grouped3$total_PSUs
    
    
    ggplot(data = df_cut_grouped3, aes(x=EventForce, y=prop, fill=Alliance)) +
      geom_bar(stat="identity", position=position_dodge()) + 
      ylim(0,1) +
      theme(axis.text.x=element_text(angle=45,hjust=1, size=10)) +
      labs(title = paste("Proportion of resources deployed to event from Alliance or Elsewhere"),
           subtitle = paste0("Results for simulations of ", num_events, " x ", event_size ," SoU"),
           y = "Proportion of resources deployed",
           x = "Seat of Unrest Location",
           caption = paste("\n\nGenerating Script:", print(rstudioapi::getActiveDocumentContext()$path))) 
    
    ggsave(file = paste0("../Alliance_Split_", event_size, "x", num_events, "SoU.pdf"), height = 6, width = 11)
  }
}

#note, as number of large events increases the proportion of PSUs coming from alliance increases - as you have to rely on yourself 

#----------------------------------------------------------------------------------------------------------------

