## 6. Data Architecture
For the MVP, we will store data in structured JSON files and put them in the content/ directory. This makes GitHub-based review and updates more convenient.

There are four main types of data: opportunities, events, programs, and resources.

## 7. Backend

For the MVP, we will not deploy a runtime backend because the website will use static JSON data and client-side search and filtering. A backend such as FastAPI can be considered in the future if the project requires dynamic data, user authentication, or external integrations.
