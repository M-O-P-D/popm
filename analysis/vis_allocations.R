#----------------------------------------------------------------------------------------------------------------------
#Look at how resources are distributed 
#----------------------------------------------------------------------------------------------------------------------
library(tidyverse)
library(gridExtra)
library(rstudioapi)  
library(ggforce)


#REMEMBER TO SET YOUR WORKING DIRECTORY 
root_path_results <- getwd()
setwd(root_path_results)


#USER PARAM
n_events <- 10
shift_allocation <- 100
large_event_PSUs <- 99
medium_event_PSUs <- 35
small_event_PSUs <- 15


num_events <- 3
event_size <- "medium"

#Step through all model conditions - numbers of SoU
pdf(paste0("AggregateOut/Who-gets-what-from-where.pdf"), height = 12, width = 8)

for(num_events in 1:n_events) 
{

  #Load data 
  setwd(paste0(root_path_results, "/", num_events, "events"))
  df <- read_csv(paste0(num_events,"events_allocations.csv"))
  head(df)
  df <- df[,c('EventForce','AssignedForce', 'Alliance', 'PSUs','Requirement')]

  #flag when responses are from your own PFA, a regional ally, or a national response
  df$Alliance[df$EventForce == df$AssignedForce] <- 'Home'
  df$Alliance[df$Alliance == 'TRUE'] <- 'Regional' 
  df$Alliance[df$Alliance == 'FALSE'] <- 'National' 
  
  head(df)
  df$EventForce <- as_factor(df$EventForce)
  df$AssignedForce <- factor(as.character(df$AssignedForce))
  df <- df %>% arrange(AssignedForce)
  
  
  #Step through all model conditions - size of SoU
  for(event_size in c("small","medium","large"))
  {
    #large events 
    if(event_size == "small") {df_cut <- filter(df, Requirement == small_event_PSUs)}
    if(event_size == "medium") {df_cut <- filter(df, Requirement == medium_event_PSUs)}
    if(event_size == "large") {df_cut <- filter(df, Requirement == large_event_PSUs)}
    
    
    df_cut <- df_cut %>% 
      group_by(EventForce, AssignedForce, Alliance) %>% 
      summarise(
        sum = sum(PSUs),
        )
    
    df_cut_totals <- df_cut[,c('EventForce', 'sum')] %>% 
      group_by(EventForce) %>% 
      summarise(
        sum = sum(sum),
      )


    df_results <- merge(df_cut,df_cut_totals, by='EventForce')
    df_results$proportion_resources <- round((df_results$sum.x/df_results$sum.y) * 100,digits = 2)
    df_results
    
    #visualise who exports to who

    for (i in 1:5){
      print(ggplot(data = df_results, aes(x=AssignedForce, y=proportion_resources, fill = Alliance)) +
      geom_bar(stat="identity") + 
      theme(axis.text.x=element_text(angle=45,hjust=1, size=6)) +
      labs(title = paste(""),
           subtitle = paste("Analsyses of" , num_events , "x" ,event_size, "SoU Scenarios"),
           y = "% of resource provided") +
    facet_wrap_paginate(~EventForce, ncol = 1, nrow =8, page = i))
    }
  }
}
  
dev.off()
    
    
    
#SPEAK TO ANDREW ABOUT TOTAL COUNTS LOGIC .... 
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
#         
#     
#     #First visualise top exporters
#     p1 <- ggplot(data = df_cut, aes(x=AssignedForce, y=mean)) +
#       geom_bar(stat="identity", position=position_dodge()) + 
#       #geom_errorbar(aes(ymin=mean-sd, ymax=mean+sd), width=.2,position=position_dodge(.9)) +
#       theme(axis.text.x=element_text(angle=45,hjust=1, size=10)) +
#       labs(title = paste("AAAAAAA Top Exporters of PSUs"),
#            subtitle = paste("Analsyses of" , num_events , "x" ,event_size, "SoU Scenarios"),
#            y = "Mean number of PSUs sent to events",
#            caption = paste("\n\nGenerating Script:", print(rstudioapi::getActiveDocumentContext()$path))) 
#     
#     
#     
#     
#     #Then breakdown by Event Location - for events occuring in a particular PFA - from where do they typically get their PSUs
#     for (i in 1:10)
#     {
#       ggplot(data = df_cut, aes(x=AssignedForce, y=mean_prop)) +
#         geom_bar(stat="identity", position=position_dodge()) + 
#         theme(axis.text.x=element_text(angle=45,hjust=1, size=8)) +
#         labs(title = paste("Who gets what from where?"),
#              subtitle = paste("Analsyses of PSU providers by Event Location - " , event_size, "x", num_events, " SoU Scenarios"),
#              y = "Mean proportion of PSUs sent to events",
#              x = "Provider of Resource") +
#         facet_wrap_paginate(~EventForce, ncol = 3, nrow = 3, page = i)
#       
#       ggsave(file = paste0("../Who_gets_what_from_where_", event_size, "x", num_events, "SoU_p", i, ".pdf"), height = 6, width = 11)
#     }  
#   }
# }
# 
# 
# 
# #----------------------------------------------------------------------------------------------------------------
# #Do you get from your alliance or from elsewhere?
# #----------------------------------------------------------------------------------------------------------------
# 
# n_events <- 10
# 
# for(num_events in 1:n_events) 
# {
#   setwd(paste0("../", num_events, " Events"))
#   df <- read_csv(paste0(num_events,"events_allocations.csv"))
#   head(df)
#   
#   df$proportion_req = df$PSUs/df$Requirement
#   df
#   
#   
#   for(event_size in c("small","medium","large"))
#   {
#     #large events 
#     if(event_size == "small") {df_cut <- filter(df, Requirement == 20)}
#     if(event_size == "medium") {df_cut <- filter(df, Requirement == 80)}
#     if(event_size == "large") {df_cut <- filter(df, Requirement == 200)}
#     
#     df_cut
#     
#     #This sums across all simulations how many PSUs have been provided by self/alliance and how many from outside  
#     df_cut_grouped <- df_cut %>% 
#       group_by(EventForce, Alliance) %>% 
#       summarise(
#         sum_PSUs = sum(proportion_req)
#       )
#     
#     #now work out the total number of PSUs supllied in general 
#     df_cut_grouped2 <-     df_cut_grouped %>% 
#       group_by(EventForce) %>% 
#       summarise(
#         total_PSUs = sum(sum_PSUs)
#       )
#     
#     
#     #Merge the two files - and calc what proportion of total PSUs recieved across all models come from alliance or otherwise.
#     df_cut_grouped3 <- merge(df_cut_grouped, df_cut_grouped2, by = "EventForce")
#     df_cut_grouped3$prop <- df_cut_grouped3$sum_PSUs/df_cut_grouped3$total_PSUs
#     
#     
#     ggplot(data = df_cut_grouped3, aes(x=EventForce, y=prop, fill=Alliance)) +
#       geom_bar(stat="identity", position=position_dodge()) + 
#       ylim(0,1) +
#       theme(axis.text.x=element_text(angle=45,hjust=1, size=10)) +
#       labs(title = paste("Proportion of resources deployed to event from Alliance or Elsewhere"),
#            subtitle = paste0("Results for simulations of ", num_events, " x ", event_size ," SoU"),
#            y = "Proportion of resources deployed",
#            x = "Seat of Unrest Location",
#            caption = paste("\n\nGenerating Script:", print(rstudioapi::getActiveDocumentContext()$path))) 
#     
#     ggsave(file = paste0("../Alliance_Split_", event_size, "x", num_events, "SoU.pdf"), height = 6, width = 11)
#   }
# }
# 
# #note, as number of large events increases the proportion of PSUs coming from alliance increases - as you have to rely on yourself 
# 
# #----------------------------------------------------------------------------------------------------------------
# 
