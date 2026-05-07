# G10 Bristol Food Network

Digital marketplace platform for the Bristol Regional Food Network case study. The system connects local food producers with customers, community groups, and restaurants. It supports product browsing, producer product management, cart and checkout, multi-vendor orders, order tracking, stock management, settlements, sustainability features, and community engagement features.

This project was built for the **Distributed and Enterprise Software Development** group project using Django, PostgreSQL, Docker, and Nginx.

---

## Contents

- [Project Overview](#project-overview)
- [Main Features](#main-features)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Setup Instructions](#setup-instructions)
- [Running the Application](#running-the-application)
- [Database Commands](#database-commands)
- [Useful URLs](#useful-urls)
- [Test Payment Details](#test-payment-details)
- [Test Case Coverage](#test-case-coverage)
- [Troubleshooting](#troubleshooting)
- [Assessment Submission Checklist](#assessment-submission-checklist)

---

## Project Overview

The Bristol Regional Food Network marketplace is designed to help local producers sell food products online and allow customers to buy from one or multiple producers in a single shopping experience.

The application includes different user roles:

- **Producers** can register, list products, update stock, manage orders, mark surplus products, create recipes, create farm stories, and view payment/settlement information.
- **Customers** can register, browse products, search/filter products, add items to cart, checkout, view order history, reorder items, and leave reviews.
- **Community groups** can register as institutional customers and place larger/bulk orders through the standard checkout flow.
- **Restaurants** can register as business customers and manage recurring weekly/fortnightly orders.
- **Administrators** can access Django admin and commission reporting features.

---

## Main Features

### User Accounts and Security

- Producer registration
- Customer registration
- Community group registration
- Restaurant registration
- Email-based login
- Logout and session handling
- Role-based access control
- Producer-only pages protected from customers
- Customer-only checkout/order pages protected from producers
- Django password validation and password hashing

### Product Marketplace

- Marketplace homepage with product cards
- Product detail pages
- Category browsing
- Product search
- Organic certification filter
- Seasonal availability indicators
- Harvest date display
- Farm/producer information
- Allergen warnings
- Product images
- Stock visibility

### Producer Product Management

- Add products
- Edit products
- Delete products
- Update stock quantity
- Set low stock threshold
- Set seasonal start/end months
- Set allergen information
- Set organic certification details
- Mark products as surplus deals with discounts

### Cart and Checkout

- Add products to cart
- Update item quantities
- Remove items from cart
- Multi-vendor cart grouping by producer
- Single-producer checkout
- Multi-producer checkout
- 48-hour delivery lead-time validation
- Mock/test payment validation
- Stripe test checkout support
- Order confirmation page
- Stock deduction after checkout
- 5% network commission calculation
- 95% producer payment calculation

### Orders and Producer Dashboard

- Producer incoming order dashboard
- Customer order history
- Reorder previous purchases
- Producer order detail page
- Order status updates
- Logical status flow: Pending → Confirmed → Ready → Delivered
- Status notes
- Order totals and itemised breakdowns

### Financial and Admin Features

- Weekly producer settlement view
- CSV export for producer financial records
- Network commission reporting
- 5% commission calculation
- Producer payout calculation
- Admin-only commission report page

### Sustainability and Community Features

- Food miles calculation using customer postcode and producer location data
- 20-mile local food radius support
- Surplus produce discount listings
- Farm stories
- Seasonal recipes
- Product reviews and ratings
- Verified-purchase review checks
- Low stock notifications for producers

---

## Technology Stack

- **Backend:** Django 6
- **API Support:** Django REST Framework
- **Database:** PostgreSQL
- **Containerisation:** Docker and Docker Compose
- **Web Server / Proxy:** Nginx
- **Frontend:** Django templates, HTML, CSS, JavaScript
- **Image Uploads:** Pillow
- **Payments:** Stripe test mode / mock payment validation
- **Language:** Python

---

## Repository Structure

```text
g10-bristol-food-network/
│
├── core/                         # Django project settings and URLs
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── marketplace/                  # Main Django marketplace app
│   ├── models.py                 # User, Product, Cart, Order, Review, etc.
│   ├── views.py                  # Main view/controller logic
│   ├── forms.py                  # Django forms and validation
│   ├── urls.py                   # Marketplace URL routing
│   ├── admin.py                  # Admin registration
│   ├── serializers.py            # API serializers
│   ├── migrations/               # Database migrations
│   └── templates/                # HTML templates
│
├── media/                        # Uploaded product/story/recipe images
├── nginx/                        # Nginx configuration
├── staticfiles/                  # Static files
├── Dockerfile                    # Django web container
├── docker-compose.yml            # Multi-container setup
├── requirements.txt              # Python dependencies
├── manage.py                     # Django management script
└── README.md                     # Project setup and running instructions
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/a2-musallam/g10-bristol-food-network.git
cd g10-bristol-food-network
```

### 2. Create or check the `.env` file

The project uses Docker Compose with a PostgreSQL database. Make sure a `.env` file exists in the project root.

Example `.env` file:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=postgres

DJANGO_SECRET=change-this-for-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,web
```

Do not use real payment details or production secrets for this coursework project.

---

## Running the Application

### 1. Build and start the containers

```bash
docker compose up --build
```

The application should be available at:

```text
http://localhost:8000/
```

### 2. Run database migrations

Open a second terminal in the project folder and run:

```bash
docker compose exec web python manage.py migrate
```

### 3. Create an admin user

```bash
docker compose exec web python manage.py createsuperuser
```

### 4. Optional: collect static files

```bash
docker compose exec web python manage.py collectstatic --noinput
```

---

## Database Commands

### Make migrations after model changes

```bash
docker compose exec web python manage.py makemigrations
```

### Apply migrations

```bash
docker compose exec web python manage.py migrate
```

### Open Django shell

```bash
docker compose exec web python manage.py shell
```

### Create superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### Reset the Docker database volume

Only use this if you are happy to delete the local database data.

```bash
docker compose down -v
docker compose up --build
```

Then run migrations again:

```bash
docker compose exec web python manage.py migrate
```

---

## Useful URLs

| Page | URL |
|---|---|
| Marketplace homepage | `http://localhost:8000/` |
| Login | `http://localhost:8000/login/` |
| Producer registration | `http://localhost:8000/register/producer/` |
| Customer registration | `http://localhost:8000/register/customer/` |
| Community group registration | `http://localhost:8000/register/community-group/` |
| Restaurant registration | `http://localhost:8000/register/restaurant/` |
| Cart | `http://localhost:8000/cart/` |
| Checkout | `http://localhost:8000/checkout/` |
| Customer orders | `http://localhost:8000/orders/` |
| Producer products | `http://localhost:8000/producer/products/` |
| Producer orders | `http://localhost:8000/producer/orders/` |
| Producer finances | `http://localhost:8000/producer/finances/` |
| Producer notifications | `http://localhost:8000/producer/notifications/` |
| Surplus deals | `http://localhost:8000/surplus-deals/` |
| Farm stories | `http://localhost:8000/farm-stories/` |
| Network commission report | `http://localhost:8000/network-commission/` |
| Django admin | `http://localhost:8000/admin/` |

---

## Test Payment Details

The system is designed for test/demo payment use only.

For the mock card form, use:

```text
Card number: 4242424242424242
Expiry date: 12/34
CVV: 123
```

No real payment or real financial data should be used.

---

## Test Case Coverage

The project was developed using the official Bristol Regional Food Network test cases as the main functional guide.

| Test Case | Requirement | Status |
|---|---|---|
| TC-001 | Producer account registration | Implemented |
| TC-002 | Customer account registration | Implemented |
| TC-003 | Producer can list new products | Implemented |
| TC-004 | Customer can browse products by category | Implemented |
| TC-005 | Customer can search for products | Implemented |
| TC-006 | Customer can add products to shopping cart | Implemented |
| TC-007 | Customer can place an order from a single producer | Implemented |
| TC-008 | Customer can place a multi-vendor order | Implemented |
| TC-009 | Producer can view incoming orders | Implemented |
| TC-010 | Producer can update order status | Implemented |
| TC-011 | Producer can update product inventory | Implemented |
| TC-012 | Producer can view weekly payment settlements and export CSV reports | Implemented |
| TC-013 | Customer can view food miles for products | Implemented |
| TC-014 | Customer can filter products by organic certification | Implemented |
| TC-015 | Customer can see allergen warnings | Implemented |
| TC-016 | Producer can set seasonal availability | Implemented |
| TC-017 | Community group can place bulk orders | Implemented through community group accounts and bulk checkout support |
| TC-018 | Restaurant can establish recurring weekly orders | Implemented through restaurant recurring order management |
| TC-019 | Producer can offer surplus produce discounts | Implemented |
| TC-020 | Producer can share recipes and farm stories | Implemented |
| TC-021 | Customer can view order history and reorder products | Implemented |
| TC-022 | Secure authentication and role-based authorisation | Implemented |
| TC-023 | Producer receives low stock notifications | Implemented |
| TC-024 | Customer can rate and review products | Implemented |
| TC-025 | Administrator can monitor commission calculations | Implemented |

---

## Troubleshooting

### Error: column does not exist

This usually means migrations have not been applied after pulling new code.

Run:

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Error: database connection failed

Make sure Docker is running and the database container is healthy:

```bash
docker compose ps
```

Restart the containers:

```bash
docker compose down
docker compose up --build
```

### Error: port already in use

If port `8000` is already being used, stop the other process or change the port in `docker-compose.yml`.

### Static files or images not showing

Run:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

Also make sure the `media/` folder exists and uploaded images are being saved correctly.

### Login works but role pages are blocked

Make sure the account has the correct role:

- Producer accounts need `is_producer=True`
- Customer accounts need `is_customer=True`
- Restaurant accounts need `is_restaurant=True`
- Community group accounts need `is_community_group=True`

This can be checked in Django admin.

---

## Assessment Submission Checklist

This repository includes the required submission items for the Distributed and Enterprise Software Development group project:

- Complete Django source code for the Bristol Regional Food Network marketplace.
- Docker containerisation using `Dockerfile` and `docker-compose.yml`.
- Multi-container architecture with Django web app, PostgreSQL database, and Nginx.
- README setup and running instructions.
- Database migration and admin setup commands.
- Test case coverage summary based on the provided assessment test cases.
- Git commit history showing individual contributions from group members.
- Signed contribution matrix submitted separately as required by the module.

---

## Notes for Demonstration

During the final demo, the system can be shown using the following flow:

1. Register or log in as a producer.
2. Add products with stock, allergens, seasonal availability, and organic certification.
3. Register or log in as a customer.
4. Browse, search, filter, and view product details.
5. Add products from one or more producers to the cart.
6. Complete checkout using test payment details.
7. Show the customer order history and reorder feature.
8. Log in as a producer and update order status.
9. Show stock reduction and low stock notifications.
10. Show surplus deals, farm stories, recipes, reviews, food miles, and commission reporting.

---

## Contributors

This project was developed by Group 10 as part of the Distributed and Enterprise Software Development module.

Individual contribution percentages are recorded in the signed contribution matrix.

Abdullah Musallam
Benjamin Smith
Hasibe Erdogan
Jc Mendoza

