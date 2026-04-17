# HomeMadeCandle Testing

This document describes basic testing of the project at the level of a simple starter set.  
The goal is not full coverage, but verification of the main scenarios after code changes.

## Tools Used

- `pytest` as the testing framework  
- Flask test client for HTTP requests without running a real server  
- separate SQLite database for tests  

## Test Structure

- `tests/conftest.py` — creation of the test application, client, and test data  
- `tests/test_public_routes.py` — basic checks of pages and healthcheck  
- `tests/test_cart.py` — adding, updating, and removing items in the cart  
- `tests/test_checkout.py` — simple checkout scenarios  

## Currently Covered

- opening main public pages without `500` error  
- healthcheck endpoint works  
- adding a product to the cart  
- adding a composition to the cart  
- updating item quantity in the cart  
- removing an item from the cart  
- creating an order from a product  
- creating an order from a composition  
- redirect to the cart if checkout is called with an empty cart  

## Not Yet Covered

- full phone validation check  
- administrator authorization  
- uploading images to Supabase  
- actual sending of messages to Telegram  
- integration with Nova Poshta API  
- browser-based UI/E2E tests  

## Running Tests

1. Activate the virtual environment.  
2. Install application dependencies and `pytest`.

```bash
pip install -r requirements.txt
pip install pytest
