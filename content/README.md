# Content

This directory holds content assets and source markdown files for the digital experience.

Use it for blog posts, knowledge base entries, landing-page copy, or structured content that the app can render.

# WIT-Hub Architecture


## 1. Project Overview
WIT-Hub is a website for Georgia Tech female students and the broader Georgia Tech community that brings together multiple resources to support students. The website collects opportunities, events, programs, and other resources, allowing users to view, search, and filter information.

## 2. Frontend

## 3. Backend
For the MVP, WIT-Hub will not use a deployed runtime backend. The website will use structured JSON files as the content source, which the frontend can access directly. A backend may be added in the future if the project needs features such as user authentication, dynamic content editing, external integrations, or server-side search.

## 4. Database
For the MVP, data will be stored in structured JSON files because the project currently has a relatively small amount of data. A database such as PostgreSQL can be considered in the future if more data is added or more complex data operations are needed.

## 5. Hosting & Deployment
Currently, we plan to use Cloudflare Pages for hosting and GitHub for version control and deployment. The website will be automatically built and deployed when changes are pushed to GitHub.


# WIT-Hub Content Data Model
WIT-Hub organizes its content into four main types:
- Opportunities
- Events
- Programs
- Resources

## 1. Opportunity
An opportunity should include the following fields:

Required fields
- id: (String) A unique identifier for each opportunity.
- title: (String) The title of the opportunity.
- organization: (String) The organization that offers the opportunity.
- description: (String) A detailed description of the opportunity.
- type: (String) Helps users filter opportunities by category, such as Internship, Scholarship, or Competition.
- url: (String) The main link to the official opportunity or application page.
- source: (String) Indicates where the information comes from.
- last_updated: (Date) The date when the information was last updated.

Optional fields
- location: (String) The location of the opportunity if it is in person.
- deadline: (Date) The application deadline, if applicable.
- eligibility: (Array of Strings) Prerequisites or eligibility requirements for the opportunity.
- tags: (Array of Strings) Keywords that help users search for and filter opportunities.

## 2. Event
An event should include the following fields:

Required fields
- id: (String) A unique identifier for each event.
- title: (String) The title of the event.
- organization: (String) The organization that hosts the event.
- description: (String) A detailed description of the event.
- date: (Date) The date when the event takes place.
- url: (String) The main link to the official event page.
- source: (String) Indicates where the information comes from.
- last_updated: (Date) The date when the information was last updated.

Optional fields
- time: (String) The time when the event takes place.
- location: (String) The location of the event if it is in person.
- eligibility: (Array of Strings) Eligibility requirements for attending the event.
- tags: (Array of Strings) Keywords that help users search for and filter events.
- recurrence: (String) Indicates whether the event occurs repeatedly.


## 3. Program
A program should include the following fields:

Required fields: 
- id: (String) A unique identifier for each program.
- title: (String) The title of the program.
- organization: (String) The organization that offers the program.
- description: (String) A detailed description of the program.
- type: (String) The type of program, such as Mentorship, Workshop, or Fellowship.
- url: (String) The main link to the official program page.
- source: (String) Indicates where the information comes from.
- last_updated: (Date) The date when the information was last updated.

Optional fields: 
- location: (String) The location of the program if it is in person.
- deadline: (Date) The application deadline, if applicable.
- eligibility: (Array of Strings) Eligibility requirements for participating in the program.
- tags: (Array of Strings) Keywords that help users search for and filter programs.

## 4. Resource
A resource should include the following fields:

Required fields:
- id: (String) A unique identifier for each resource.
- title: (String) The title of the resource.
- description: (String) A detailed description of the resource.
- type: (String) The type of resource, such as Guide, Website, or Article.
- url: (String) The main link to the resource.
- source: (String) Indicates where the information comes from.
- last_updated: (Date) The date when the information was last updated.

Optional fields:
- tags: (Array of Strings) Keywords that help users search for and filter resources.

## 6. Data Architecture
For the MVP, we will store data in structured JSON files and put them in the content/ directory. This makes GitHub-based review and updates more convenient.

There are four main types of data: opportunities, events, programs, and resources.

## 7. Backend

For the MVP, we will not deploy a runtime backend because the website will use static JSON data and client-side search and filtering. A backend such as FastAPI can be considered in the future if the project requires dynamic data, user authentication, or external integrations.
