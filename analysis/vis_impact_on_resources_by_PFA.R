#----------------------------------------------------------------------------------------------------------------------
#Look at overall performance 
#- i.e. plot number of events, and percentage of scenarios fully resourced - facet by event size
#------------------------------------------------------------------
library(tidyverse)
library(gridExtra)
library(reshape2)

#REMEMBER TO SET YOUR WORKING DIRECTORY 
root_path_results <- getwd()
setwd(root_path_results)

#USER PARAM
n_events <- 10
shift_allocation <- 100
large_event_PSUs <- 99
medium_event_PSUs <- 35
small_event_PSUs <- 15




#THERE ARE MULTIPLE WAYS TO THINK ABOUT THE IMPACT OF SoU on OTHER AREAS OF POLICING - HERE WE EXPLORE 2. 
#The first asks the question how close are the 6 core areas of policing to the minimum requirements after 
# responding in various scenarios - by PFA. This allows us to answer the question when and who gets really stretched?

#The second simply asks each PFA what proportion of your original resources are left in each of the core six areas after
#public order resources have been dispatched to respond. This let's us ask who gives up the most/least? 

#METHOD 1 - REPORT THE RATIO OVER AND ABOVE THE MINIMUM REQUIRMENT IN A CORE FUNCTION AREA 

#set working directory 
setwd(paste0(root_path_results, "/", num_events, "events"))

#load resources delta (each row represents any PFA stock if they have changed in the current sim)
resources_delta <- read_csv(paste0(num_events,"events_resources.csv"))
#load resources baseline 
resources_baseline <- read_csv(paste0(num_events,"events_resources_baseline.csv"))
#factorise the PFA names 
resources_delta$name <- as_factor(resources_delta$name)
resources_baseline$name <- as_factor(resources_baseline$name)

#now need to get the size of events at each RunID
#Load event file
events <- read_csv(paste0(num_events,"events.csv"))
#only look at the first hour of immediate events 
events <- filter(events, Time == 0 & EventStart == 0)
#drop irrelevant cols
events <- events[,c('RunId','Required')]
#now group by to get a list of runIDs and resource requirements 
event_requirements  <- unique(events)

#now merge that with the resources delta file 
resources_delta <- merge(resources_delta, event_requirements, by = "RunId")
head(resources_delta)


#derive new columns that calc the ratio of core resourcing areas remaining after allocation - 1 = core area @ minimum
resources_delta$prop_emergency <- (resources_delta$emergency / resources_delta$emergency_MIN)
resources_delta$prop_firearms <- (resources_delta$firearms / resources_delta$firearms_MIN)
resources_delta$prop_major_incident <- (resources_delta$major_incident / resources_delta$major_incident_MIN)
resources_delta$prop_serious_crime <- (resources_delta$serious_crime / resources_delta$serious_crime_MIN)
resources_delta$prop_custody <- (resources_delta$custody / resources_delta$custody_MIN)

#now subset the relevant columns 
resources_delta_to_melt <- resources_delta[,c('RunId', 'name', 'Required','prop_emergency','prop_firearms','prop_major_incident','prop_serious_crime','prop_custody')]
head(resources_delta_to_melt)

#ensure Event levels for resources_delta_to_melt$name are in alphabetical order and then order by name- for consistency in plotting order
resources_delta_to_melt$name <- factor(as.character(resources_delta_to_melt$name))
resources_delta_to_melt <- resources_delta_to_melt %>% arrange(name)

#create datasets for different size events 
resources_delta_to_melt_small_events <- filter(resources_delta_to_melt, Required == (small_event_PSUs * 25))
resources_delta_to_melt_medium_events <- filter(resources_delta_to_melt, Required == (medium_event_PSUs * 25))
resources_delta_to_melt_large_events <- filter(resources_delta_to_melt, Required == (large_event_PSUs * 25))

#now summarise impact on PFAs in small event scenarios - mean and sd of ratios after resourcing

#DOES THIS MAKE SENSE? WHAT HAPPENS WHEN A PFA DOESN'T HELP 90% OF THE TIME - WHAT IS HERE ONLY REPRESNTS THE TIMES RESOURCES ARE USED - look at N

resources_small_events_summary <- resources_delta_to_melt_small_events %>% 
  group_by(name) %>% 
  summarise(
    n = n(), 
    mean_prop_emergency = mean(prop_emergency),
    mean_prop_firearms = mean(prop_firearms),
    mean_prop_major_incident = mean(prop_major_incident),
    mean_prop_serious_crime = mean(prop_serious_crime),
    mean_prop_custody = mean(prop_custody))

resources_medium_events_summary <- resources_delta_to_melt_medium_events %>% 
  group_by(name) %>% 
  summarise(
    mean_prop_emergency = mean(prop_emergency),
    mean_prop_firearms = mean(prop_firearms),
    mean_prop_major_incident = mean(prop_major_incident),
    mean_prop_serious_crime = mean(prop_serious_crime),
    mean_prop_custody = mean(prop_custody))

resources_large_events_summary <- resources_delta_to_melt_large_events %>% 
  group_by(name) %>% 
  summarise(
    mean_prop_emergency = mean(prop_emergency),
    mean_prop_firearms = mean(prop_firearms),
    mean_prop_major_incident = mean(prop_major_incident),
    mean_prop_serious_crime = mean(prop_serious_crime),
    mean_prop_custody = mean(prop_custody))

    

melt_large <- resources_large_events_summary %>% melt(id.vars=c("name"))

p1 <- ggplot(melt_large, aes(x=name , y=value, fill=variable)) +
  geom_bar(stat="identity", position = "dodge") +
  geom_hline(yintercept=1, linetype="dashed", color = "blue") +
  theme(axis.text.x=element_text(angle=45,hjust=1)) 
  #facet_wrap(~variable)
p1















#METHOD 2 - REPORT THE PROPORTION OF CORE FUNCTION AREA AVAILBLE AFTER ALLOCATION (TELLS YOU NOTHING ABOUT HOW CLOSE YOU ARE TO MINIMUN)

pdf(paste0("AggregateOut/RESOURCE-IMPACT-TEST-B.pdf"), height = 11, width = 11)

for(num_events in 1:n_events) 
{



#set working directory 
setwd(paste0(root_path_results, "/", num_events, "events"))

#load resources delta (each row represents any PFA stock if they have changed in the current sim)
resources_delta <- read_csv(paste0(num_events,"events_resources.csv"))
#load resources baseline 
resources_baseline <- read_csv(paste0(num_events,"events_resources_baseline.csv"))
#factorise the PFA names 
resources_delta$name <- as_factor(resources_delta$name)
resources_baseline$name <- as_factor(resources_baseline$name)

#now need to get the size of events at each RunID
#Load event file
events <- read_csv(paste0(num_events,"events.csv"))
#only look at the first hour of immediate events 
events <- filter(events, Time == 0 & EventStart == 0)
#drop irrelevant cols
events <- events[,c('RunId','Required')]
#now group by to get a list of runIDs and resource requirements 
event_requirements  <- unique(events)

#now merge that with the resources delta file 
resources_delta <- merge(resources_delta, event_requirements, by = "RunId")
head(resources_delta)

#join original resources
resources_delta_X <- merge(resources_delta, resources_baseline, by = "name")

resources_delta_X$emergency_prop <-  resources_delta_X$emergency.y - resources_delta_X$emergency.x 
resources_delta_X$firearms_prop <-  resources_delta_X$firearms.y - resources_delta_X$firearms.x 
resources_delta_X$major_incident_prop <-  resources_delta_X$major_incident.y - resources_delta_X$major_incident.x 
resources_delta_X$public_order_prop <-  resources_delta_X$public_order.y - resources_delta_X$public_order.x 
resources_delta_X$serious_crime_prop <-  resources_delta_X$serious_crime.y - resources_delta_X$serious_crime.x 
resources_delta_X$custody_prop <-  resources_delta_X$custody.y - resources_delta_X$custody.x 

head(resources_delta_X)

resources_delta_X_to_melt <- resources_delta_X[,c('RunId', 'name', 'Required','emergency_prop','firearms_prop','major_incident_prop','public_order_prop','serious_crime_prop','custody_prop')]

head(resources_delta_X_to_melt)

#ensure Event levels for resources_delta_to_melt$name are in alphabetical order and then order by name- for consistency in plotting order
resources_delta_X_to_melt$name <- factor(as.character(resources_delta_X_to_melt$name))
resources_delta_X_to_melt <- resources_delta_X_to_melt %>% arrange(name)

#create datasets for different size events 
resources_delta_X_to_melt_small_events <- filter(resources_delta_X_to_melt, Required == (small_event_PSUs * 25))
resources_delta_X_to_melt_medium_events <- filter(resources_delta_X_to_melt, Required == (medium_event_PSUs * 25))
resources_delta_X_to_melt_large_events <- filter(resources_delta_X_to_melt, Required == (large_event_PSUs * 25))


resources_small_events_summary <- resources_delta_X_to_melt_small_events %>% 
  group_by(name) %>% 
  summarise(
    mean_emergency_prop = mean(emergency_prop),
    mean_firearms_prop = mean(firearms_prop),
    mean_major_incident_prop = mean(major_incident_prop),
    mean_public_order_prop = mean(public_order_prop),
    mean_serious_crime_prop = mean(serious_crime_prop),
    mean_custody_prop = mean(custody_prop))

resources_medium_events_summary <- resources_delta_X_to_melt_medium_events %>% 
  group_by(name) %>% 
  summarise(
    mean_emergency_prop = mean(emergency_prop),
    mean_firearms_prop = mean(firearms_prop),
    mean_major_incident_prop = mean(major_incident_prop),
    mean_public_order_prop = mean(public_order_prop),
    mean_serious_crime_prop = mean(serious_crime_prop),
    mean_custody_prop = mean(custody_prop))

resources_large_events_summary <- resources_delta_X_to_melt_large_events %>% 
  group_by(name) %>% 
  summarise(
    mean_emergency_prop = mean(emergency_prop),
    mean_firearms_prop = mean(firearms_prop),
    mean_major_incident_prop = mean(major_incident_prop),
    mean_public_order_prop = mean(public_order_prop),
    mean_serious_crime_prop = mean(serious_crime_prop),
    mean_custody_prop = mean(custody_prop))


melt_large <- resources_large_events_summary %>% melt(id.vars=c("name"))
melt_medium <- resources_medium_events_summary %>% melt(id.vars=c("name"))
melt_small <- resources_small_events_summary %>% melt(id.vars=c("name"))

# p1 <- ggplot(melt_large, aes(x=name , y=value)) +
#   geom_bar(stat="identity", position = "dodge") +
#   labs(title = paste("Simulating", num_events, "Large Simultaneous SoU"),
#         y = "Mean number of PO officers provided from core area") +
#   theme(axis.text.x=element_text(angle=45,hjust=1, size=6)) +
#   facet_wrap(~variable)
# 
# p2 <- ggplot(melt_medium, aes(x=name , y=value)) +
#   geom_bar(stat="identity", position = "dodge") +
#   labs(title = paste("Simulating", num_events, "Medium Simultaneous SoU"),
#        y = "Mean number of PO officers provided from core area") +
#   theme(axis.text.x=element_text(angle=45,hjust=1, size=6)) +
#   facet_wrap(~variable)
# 
# p3 <- ggplot(melt_small, aes(x=name , y=value)) +
#   geom_bar(stat="identity", position = "dodge") +
#   labs(title = paste("Simulating", num_events, "Small Simultaneous SoU"),
#        y = "Mean number of PO officers provided from core area",
#        caption = "Simulation of 1 to 3 events - all combinations. 4+ Events - sample of 10000 combinations.") +
#   theme(axis.text.x=element_text(angle=45,hjust=1, size=6)) +
#   facet_wrap(~variable)
# 


p1 <- ggplot(melt_large, aes(x=name , y=value, fill=variable)) +
  geom_bar(stat="identity", position = "dodge") +
  labs(title = paste("Simulating", num_events, "Large Simultaneous SoU"),
       y = "Mean PO officers provided", x = "Provider Police Force Area") +
  theme(axis.text.x=element_text(angle=45,hjust=1, size=8), axis.text.y=element_text(size=6)) 

p2 <- ggplot(melt_medium, aes(x=name , y=value, fill=variable)) +
  geom_bar(stat="identity", position = "dodge") +
  labs(title = paste("Simulating", num_events, "Medium Simultaneous SoU"),
       y = "Mean PO officers provided", x = "Provider Police Force Area") +
  theme(axis.text.x=element_text(angle=45,hjust=1, size=8), axis.text.y=element_text(size=6)) 

p3 <- ggplot(melt_small, aes(x=name , y=value, fill=variable)) +
  geom_bar(stat="identity", position = "dodge") +
  labs(title = paste("Simulating", num_events, "Small Simultaneous SoU"),
       y = "Mean PO officers provided", x = "Provider Police Force Area",
       caption = "Simulation of 1 to 3 events - all combinations. 4+ Events - sample of 10000 combinations.") +
  theme(axis.text.x=element_text(angle=45,hjust=1, size=8), axis.text.y=element_text(size=6)) 






print(grid.arrange(p1,p2,p3))


}
dev.off()



