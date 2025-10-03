# Django Shopping Assistant

A    Modern e-commerce platform with AI-powered product recommendations, price alerts, and a chatbot assistant (ShopGenie) built with Django.

## Features
- Hierarchical categories and subcategories for products
- Product cards with consistent design
- Floating ShopGenie chatbot widget (uses Gemini/Google LLM)
- Price alerts with email notifications (Gmail SMTP)
- Auto-buy and cart integration for price drops
- Admin interface for products, categories, orders, and alerts
- Celery for background tasks (price alert processing)

## Setup Instructions

1. **Clone the repository**
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Create a `.env` file with your Gemini API key and any secrets.
   - Set up Gmail SMTP credentials in `settings.py` for email alerts.
4. **Run migrations:**
   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```
5. **Create a superuser:**
   ```sh
   python manage.py createsuperuser
   ```
6. **Start the development server:**
   ```sh
   python manage.py runserver
   ```
7. **Start Celery worker (for price alerts):**
   ```sh
   celery -A ecommerce worker -l info
   ```

## Usage
- Access the site at `http://127.0.0.1:8000/`
- Use the admin at `/admin/` to manage products, categories, orders, and alerts
- Try the ShopGenie chatbot on the home page or via the navbar
- Set price alerts on product pages to get notified by email when prices drop

## Customization
- Edit `settings.py` for email, API, and other configuration
- Update categories and products in the admin
- Extend the chatbot logic in `views.py` as needed

## License
MIT 
