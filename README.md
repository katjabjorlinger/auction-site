# Auction Site - Flask Web Application
## Project Overview 📌
This project is a web-based auction system built using Flask. The application allows users to browse auction items, place bids, and interact with auctioned goods. The system supports user authentication, item categorization, bid management, and question-answer functionalities for items. Additionally, the system implements email notifications for outbid alerts and bid confirmations.

## Features ✨
### Auction Item Management
* Users can create, update, and delete auction listings (admin only).
* Items are categorized into predefined categories.
* Each item includes title, description, seller, image, starting price, start time, and end time.

### Bidding System
* Users can place bids on auction items.
* The system validates bids (ensures the new bid is higher than the previous one).
* Automated email notifications are sent when a user is outbid.

### User Authentication & Authorization
* Flask-Login is used for session-based authentication.
* Users can log in and log out.
* Role-based access control: Admin, Superuser, and Regular Users.
* User data is securely stored in JSON format.

### Additional Features
* Question & Answer Section – Users can ask questions about auction items, and admins can respond.
* Search, Sorting, and Filtering – Find auctions by category, keyword, or auction status.
* Likes & Dislikes – Users can like/dislike auction items.
* Email Notifications – Get notified about bidding activity.
  
## Technologies Used 🛠️
* Backend Framework: Python Flask Blueprints for modular routing
* Database: SQLite via sqlite3 for CRUD operations
* Authentication: Flask-Login (session-based login)
* Forms & Validation: Flask-WTF for login forms
* Email Notifications: Flask-Mail for bid confirmation and outbid alerts
* Data Management:JSON for user information
* SQLite for auction items, bids, categories, and questions
* Frontend: HTML Templates with Jinja2 for rendering dynamic auction pages and Bootstrap CSS framework for responsive UI.
* Regular Expressions: Used for input validation (title, description, and seller fields)

## API Endpoints 📡		
| Method |      Endpoint      |  Description |
|:------|:----------------|:-----------------------------|
| **GET**   | `/auction/`         | View all auction items |
| **GET**   | `/auction/<id>`      | View details of a specific auction item |
| **POST**  | `/auction/bid/<id>`  | Place a bid on an item |
| **POST**  | `/auction/add`       | Add a new auction item (**admin only**) |
| **POST**  | `/auction/edit/<id>` | Edit an auction item (**admin only**) |
| **DELETE**| `/auction/delete/<id>` | Delete an auction item (**admin only**) |
| **POST**  | `/auction/like/<id>`  | Like an auction item |
| **POST**  | `/auction/dislike/<id>` | Dislike an auction item |
| **POST**  | `/auction/question/<id>` | Ask a question about an item |


## View it Live 🌍
Project can be viewed live at https://katbjdu.pythonanywhere.com/auction/
