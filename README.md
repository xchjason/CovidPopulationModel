# Contents
- 1	COVID Population Model	
- 2	Preparing the model – Steps you must take once	
  - 2A – No local installation – Using Google applications	
     - 2A.1 – Activate Google utilities	
     - 2A.2 – Create a Google folder	
  - 2B – No Google utilities – Local installation instead	
- 3	Running the model	
  - 3.1	Selecting an assumption set	
    - 3.1.1  If the training region dropdown list does contain the target region	
    - 3.1.2  If the training region dropdown list does not contain the target region	
    - 3.1.3  Selecting the training period	
  - 3.2	Adjusting assumption set values	
  - 3.3	Running the model	
    - 3.3.1  Model mode 1 – Training and target regions the same	
    - 3.3.2  Model mode 2 – Training and target regions differ, user leaves assumptions unchanged	
    - 3.3.3  Model use mode 3 – User modifies assumptions	


# 1 Covid Population Model
This repository contains the Tufts Susceptible-to-Hospital Forecasting Model for COVID-19. This mechanistic probabilistic model projects how 
- COVID prevalence in the general population may change over time; 
- Disease may progress from infection in susceptible individuals to symptomatic disease and potentially to severe disease; 
- Some individuals may undergo hospitalization; and 
- Hospitalized patients may progress from care in the general ward to more acute care (e.g., in the intensive care unit).
The model has two characteristics that make it a useful tool for estimating the contribution interventions make to population health. 

First, ***the model’s projections align with real world observations*** for a specific geographic region because the model undergoes calibration against empirical data.  Because it is probabilistic, the model characterizes its projections as distributions.  

Second, ***the model can explore an intervention’s impact*** because its mechanistic structure means that it has user-modifiable assumptions representing aspects of COVID that interventions might influence – e.g., the rate at which people become infected, the proportion of people who become sick enough to need hospital care, or how long it takes hospitalized patients to recover enough to be discharged.  The model reports outcomes useful to characterizing intervention value, including how many people become infected, develop severe disease, or die, hospital utilization, and intensive care unit utilization.

Possible research questions this model can help to address include:
- Based on observed trends in Massachusetts in April through July of the current year, how many COVID patients will hospital admit in August?
- What impact would a drug that reduces hospital admissions by 10 percent have on ICU utilization?
- How would a new COVID variant that is 10 percent more transmissible than the current dominant variant affect hospital utilization?

# 2	Preparing the model – Steps you must take once
Users have two options for setting up the model.  They can avoid installing software on their computer (the “No local installation” option), or they can avoid using Google software (the “No Google utilities” option):

- ***No local installation*** – users control the model using three Google cloud-based tools: google Sheets, Google Drive, and Google Collaboratory.  The model reports results to a Google workbook.
- ***No Google utilities*** – users use the Anaconda environment and install software on their own computer.  The model reports results to an Excel spreadsheet.  We are currently developing this option.

# 2A – No local installation – Using Google applications
Running the model requires:
- A Google spreadsheet workbook referred to as the “control workbook”;
- One of three Google COLAB notebooks, depending on what model features the user wishes to control; and
- Simulation code.
This section describes how to activate the Google utilities needed to install and run the model (Section 2A.1) and how to create and populate a folder with the required files and software (Section 2A.2).  Section 3 describes how to alter model control features and run the model.

2A.1 – Activate Google utilities
- The Google Chrome browser (available here)
- A Google Drive account (see here for instructions to set one up; and see here for more information on managing your Google Drive account).
- The Google Colaboratory application.  
  - From within your browser go to Google Drive (here); 
  - At the left, click on the “+ New” button ; 
  - Select MORE from the dropdown menu; 
  - Select + CONNECT MORE APPS; 
  - Click on the search icon at the top of the window that pops up (the magnifying glass icon) and search for “colab”.
  - lick on the “Colaboratory” application that appears.
  - Click on the blue INSTALL button.

2A.2 – Create a Google folder
Step 2A.2.1 – Create a Google folder (see instructions, here).  Name this folder BayesianCovidPopulationModel.

Step 2A.2.2 – Download the contents of the Github page located here.  To do so, click on the green CODE button in the upper right corner of the page and select DOWNLOAD ZIP from the dropdown menu.
![](image/Picture1.png)

Step 2A.2.3 – Unzip the downloaded contents.  On a Windows computer, find the downloaded Zip file, right click on it, and select EXTRACT ALL.  Note the location of the folder created and containing the contents downloaded from the Github page.

Step 2A.2.4 – Upload the material downloaded in Steps 2A.2.2 and 2A.2.3 to the Google folder created in Step 2A.2.1 (BayesianCovidPopulationModel).
- Within your internet browser, go to https://drive.google.com/drive/my-drive.  
- Find the folder created in Step 2A.2.1 (BayesianCovidPopulationModel) and double click on it.
- At the left, click on the “+ New” button.
- Select FOLDER UPLOAD.
- A file browser window will open.  Navigate to the folder on your computer created in Step 2A.2.3.  Select the folder.  Click on “upload” when prompted.

Step 2A.2.5 – Move the contents in the uploaded folder to the top level of the folder created in Step 2A.2.1.  
- Open the folder created in Step 2A.2.1 (BayesianCovidPopulationModel).  You will see a single folder.  Open that folder.  Continue to open folders until you get to a list of folders and files that resembles the figure at right. 
- Select all items in this folder by (1) clicking on the first item, (2) holding down the shift key, and (3) clicking on the final item in this list.  All items should now be highlighted.
- Move the items by (1) right clicking and selecting MOVE TO, (2) navigating to the folder created in Step 2A.2.1, and (3) clicking on the blue MOVE HERE button.

![](image/Picture2.png)

Step 2A.2.6 – Create your own copy of the Google workbook that has the model parameter values that control the simulation.
- Open the Google workbook template by clicking here; 
- Select the FILE dropdown menu and then select MAKE A COPY; 
- In the NAME box, enter a name that is meaningful to you; 
- In the folder box, double-click on the “My Drive” folder and navigate your way to the Google folder created in Step 2A.2.1.
![](image/Picture3.png)

# 2B – No Google utilities – Local installation instead
To be done.

