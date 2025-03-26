from flask import current_app as app
from datetime import datetime


class Category:
    def __init__(self, category_id, category_name, created_at=None):
        self.id = category_id
        self.name = category_name
        self.created_at = created_at

    @staticmethod
    def get(category_id):
        """Get a specific category by ID"""
        rows = app.db.execute('''
            SELECT category_id, category_name, created_at
            FROM Products_Categories
            WHERE category_id = :category_id
        ''', category_id=category_id)

        return Category(*(rows[0])) if rows else None

    @staticmethod
    def get_all():
        """Get all product categories"""
        rows = app.db.execute('''
            SELECT category_id, category_name, created_at
            FROM Products_Categories
            ORDER BY category_name
        ''')

        return [Category(*row) for row in rows]

    @staticmethod
    def get_by_name(category_name):
        """Get category by name (case insensitive)"""
        rows = app.db.execute('''
            SELECT category_id, category_name, created_at
            FROM Products_Categories
            WHERE LOWER(category_name) = LOWER(:category_name)
        ''', category_name=category_name)

        return Category(*(rows[0])) if rows else None

    @staticmethod
    def create(category_name):
        """Create a new category"""
        try:
            rows = app.db.execute('''
                INSERT INTO Products_Categories (category_name)
                VALUES (:category_name)
                RETURNING category_id, category_name, created_at
            ''', category_name=category_name)

            return Category(*(rows[0])) if rows else None
        except Exception as e:
            print(f"Error creating category: {str(e)}")
            return None

    @staticmethod
    def update(category_id, category_name):
        """Update category name"""
        try:
            rows = app.db.execute('''
                UPDATE Products_Categories
                SET category_name = :category_name
                WHERE category_id = :category_id
                RETURNING category_id, category_name, created_at
            ''', category_id=category_id, category_name=category_name)

            return Category(*(rows[0])) if rows else None
        except Exception as e:
            print(f"Error updating category: {str(e)}")
            return None

    @staticmethod
    def delete(category_id):
        """Delete a category if it has no associated products"""
        try:
            # First check if category has products
            product_count = app.db.execute('''
                SELECT COUNT(*) 
                FROM Products 
                WHERE category_id = :category_id
            ''', category_id=category_id)

            if product_count[0][0] > 0:
                return False, "Cannot delete category with associated products"

            # Delete the category
            app.db.execute('''
                DELETE FROM Products_Categories
                WHERE category_id = :category_id
            ''', category_id=category_id)

            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_with_product_counts():
        """Get all categories with their product counts"""
        rows = app.db.execute('''
            SELECT pc.category_id, pc.category_name, pc.created_at, 
                   COUNT(p.product_id) as product_count
            FROM Products_Categories pc
            LEFT JOIN Products p ON pc.category_id = p.category_id
            GROUP BY pc.category_id, pc.category_name, pc.created_at
            ORDER BY pc.category_name
        ''')

        result = []
        for row in rows:
            category = Category(row[0], row[1], row[2])
            setattr(category, 'product_count', row[3])
            result.append(category)

        return result

    def to_dict(self):
        """Convert category to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Product:
    def __init__(self, product_id, category_id, product_name, description, image,
                 owner_id, created_at=None, updated_at=None, category_name=None,
                 owner_name=None, avg_rating=None, review_count=None):
        self.id = product_id
        self.category_id = category_id
        self.name = product_name
        self.description = description
        self.image = image
        self.owner_id = owner_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.category_name = category_name
        self.owner_name = owner_name
        self.avg_rating = avg_rating
        self.review_count = review_count

    @staticmethod
    def get(product_id):
        """Get product by ID with category and owner information"""
        rows = app.db.execute('''
            SELECT p.product_id, p.category_id, p.product_name, p.description, 
                   p.image, p.owner_id, p.created_at, p.updated_at, 
                   c.category_name, CONCAT(a.first_name, ' ', a.last_name) AS owner_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.review_id) as review_count
            FROM Products p
            JOIN Products_Categories c ON p.category_id = c.category_id
            JOIN Accounts a ON p.owner_id = a.user_id
            LEFT JOIN Reviews_Feedbacks r ON p.product_id = r.product_id
            WHERE p.product_id = :product_id
            GROUP BY p.product_id, c.category_name, a.first_name, a.last_name
        ''', product_id=product_id)

        return Product(*(rows[0])) if rows else None

    @staticmethod
    def get_all(available=True):
        """Get all products"""
        rows = app.db.execute('''
            SELECT p.product_id, p.category_id, p.product_name, p.description, 
                   p.image, p.owner_id, p.created_at, p.updated_at, 
                   c.category_name, CONCAT(a.first_name, ' ', a.last_name) AS owner_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.review_id) as review_count
            FROM Products p
            JOIN Products_Categories c ON p.category_id = c.category_id
            JOIN Accounts a ON p.owner_id = a.user_id
            LEFT JOIN Reviews_Feedbacks r ON p.product_id = r.product_id
            GROUP BY p.product_id, c.category_name, a.first_name, a.last_name
            ORDER BY p.product_name
        ''')

        return [Product(*row) for row in rows]

    @staticmethod
    def get_by_category(category_id):
        """Get products by category"""
        rows = app.db.execute('''
            SELECT p.product_id, p.category_id, p.product_name, p.description, 
                   p.image, p.owner_id, p.created_at, p.updated_at, 
                   c.category_name, CONCAT(a.first_name, ' ', a.last_name) AS owner_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.review_id) as review_count
            FROM Products p
            JOIN Products_Categories c ON p.category_id = c.category_id
            JOIN Accounts a ON p.owner_id = a.user_id
            LEFT JOIN Reviews_Feedbacks r ON p.product_id = r.product_id
            WHERE p.category_id = :category_id
            GROUP BY p.product_id, c.category_name, a.first_name, a.last_name
            ORDER BY p.product_name
        ''', category_id=category_id)

        return [Product(*row) for row in rows]

    @staticmethod
    def get_by_owner(owner_id):
        """Get products created by a specific owner"""
        rows = app.db.execute('''
            SELECT p.product_id, p.category_id, p.product_name, p.description, 
                   p.image, p.owner_id, p.created_at, p.updated_at, 
                   c.category_name, CONCAT(a.first_name, ' ', a.last_name) AS owner_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.review_id) as review_count
            FROM Products p
            JOIN Products_Categories c ON p.category_id = c.category_id
            JOIN Accounts a ON p.owner_id = a.user_id
            LEFT JOIN Reviews_Feedbacks r ON p.product_id = r.product_id
            WHERE p.owner_id = :owner_id
            GROUP BY p.product_id, c.category_name, a.first_name, a.last_name
            ORDER BY p.product_name
        ''', owner_id=owner_id)

        return [Product(*row) for row in rows]

    @staticmethod
    def search(query=None, category_id=None, min_price=None, max_price=None,
               sort_by='name', sort_dir='asc', limit=12, offset=0):
        """Search for products with filters and sorting"""
        # Build the base query
        base_query = '''
            SELECT p.product_id, p.category_id, p.product_name, p.description, 
                   p.image, p.owner_id, p.created_at, p.updated_at, 
                   c.category_name, CONCAT(a.first_name, ' ', a.last_name) AS owner_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.review_id) as review_count
            FROM Products p
            JOIN Products_Categories c ON p.category_id = c.category_id
            JOIN Accounts a ON p.owner_id = a.user_id
            LEFT JOIN Reviews_Feedbacks r ON p.product_id = r.product_id
        '''

        # For price filtering, we need to join with inventory
        if min_price is not None or max_price is not None:
            base_query += '''
                JOIN (
                    SELECT product_id, MIN(unit_price) as min_price
                    FROM Inventory
                    WHERE quantity > 0
                    GROUP BY product_id
                ) i ON p.product_id = i.product_id
            '''

        # Add WHERE clause if any filters
        where_clauses = []
        params = {}

        if query:
            where_clauses.append("(p.product_name ILIKE :query OR p.description ILIKE :query)")
            params['query'] = f'%{query}%'

        if category_id:
            where_clauses.append("p.category_id = :category_id")
            params['category_id'] = category_id

        if min_price is not None:
            where_clauses.append("i.min_price >= :min_price")
            params['min_price'] = min_price

        if max_price is not None:
            where_clauses.append("i.min_price <= :max_price")
            params['max_price'] = max_price

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        # Add GROUP BY
        base_query += " GROUP BY p.product_id, c.category_name, a.first_name, a.last_name"

        # Add ORDER BY
        if sort_by == 'name':
            base_query += " ORDER BY p.product_name"
        elif sort_by == 'price':
            # For price sorting, we need inventory data
            if min_price is None and max_price is None:
                base_query = base_query.replace(
                    "FROM Products p",
                    """FROM Products p
                    LEFT JOIN (
                        SELECT product_id, MIN(unit_price) as min_price
                        FROM Inventory
                        WHERE quantity > 0
                        GROUP BY product_id
                    ) i ON p.product_id = i.product_id"""
                )
            base_query += " ORDER BY i.min_price"
        elif sort_by == 'rating':
            base_query += " ORDER BY avg_rating"
        elif sort_by == 'newest':
            base_query += " ORDER BY p.created_at"

        # Add sort direction
        if sort_dir.lower() == 'desc':
            base_query += " DESC"
        else:
            base_query += " ASC"

        # Add LIMIT and OFFSET
        base_query += " LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset

        # Execute the query
        rows = app.db.execute(base_query, **params)

        return [Product(*row) for row in rows]

    @staticmethod
    def count_search_results(query=None, category_id=None, min_price=None, max_price=None):
        """Count products matching search criteria for pagination"""
        # Build the base query
        base_query = '''
            SELECT COUNT(DISTINCT p.product_id)
            FROM Products p
        '''

        # For price filtering, we need to join with inventory
        if min_price is not None or max_price is not None:
            base_query += '''
                JOIN (
                    SELECT product_id, MIN(unit_price) as min_price
                    FROM Inventory
                    WHERE quantity > 0
                    GROUP BY product_id
                ) i ON p.product_id = i.product_id
            '''

        # Add joins for other filters
        if query:
            base_query += " JOIN Products_Categories c ON p.category_id = c.category_id"

        if category_id:
            if 'c ON' not in base_query:
                base_query += " JOIN Products_Categories c ON p.category_id = c.category_id"

        # Add WHERE clause if any filters
        where_clauses = []
        params = {}

        if query:
            where_clauses.append("(p.product_name ILIKE :query OR p.description ILIKE :query)")
            params['query'] = f'%{query}%'

        if category_id:
            where_clauses.append("p.category_id = :category_id")
            params['category_id'] = category_id

        if min_price is not None:
            where_clauses.append("i.min_price >= :min_price")
            params['min_price'] = min_price

        if max_price is not None:
            where_clauses.append("i.min_price <= :max_price")
            params['max_price'] = max_price

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        # Execute the query
        result = app.db.execute(base_query, **params)

        return result[0][0] if result else 0

    @staticmethod
    def create(category_id, product_name, description, owner_id, image=None):
        """Create a new product"""
        try:
            rows = app.db.execute('''
                INSERT INTO Products (category_id, product_name, description, image, owner_id)
                VALUES (:category_id, :product_name, :description, :image, :owner_id)
                RETURNING product_id, category_id, product_name, description, 
                          image, owner_id, created_at, updated_at
            ''', category_id=category_id, product_name=product_name,
                                  description=description, image=image, owner_id=owner_id)

            if rows:
                # Add additional fields expected by Product constructor
                product_data = list(rows[0])
                product_data.extend([None, None, None, None])  # Add extra None values for additional fields
                return Product(*product_data)
            return None
        except Exception as e:
            print(f"Error creating product: {str(e)}")
            return None

    @staticmethod
    def update(product_id, category_id=None, product_name=None, description=None, image=None):
        """Update an existing product"""
        try:
            # Build the update parts and parameters
            update_parts = []
            params = {'product_id': product_id}

            if category_id is not None:
                update_parts.append("category_id = :category_id")
                params['category_id'] = category_id

            if product_name is not None:
                update_parts.append("product_name = :product_name")
                params['product_name'] = product_name

            if description is not None:
                update_parts.append("description = :description")
                params['description'] = description

            if image is not None:
                update_parts.append("image = :image")
                params['image'] = image

            # Add the updated_at timestamp
            update_parts.append("updated_at = :updated_at")
            params['updated_at'] = datetime.utcnow()

            # If no fields to update, return the current product
            if not update_parts:
                return Product.get(product_id)

            # Execute the update
            query = f'''
                UPDATE Products
                SET {", ".join(update_parts)}
                WHERE product_id = :product_id
                RETURNING product_id, category_id, product_name, description, 
                          image, owner_id, created_at, updated_at
            '''

            rows = app.db.execute(query, **params)

            if rows:
                # Get the full product with all fields
                return Product.get(product_id)
            return None
        except Exception as e:
            print(f"Error updating product: {str(e)}")
            return None

    @staticmethod
    def delete(product_id, owner_id=None):
        """Delete a product if it has no associated orders"""
        try:
            # Check ownership if owner_id provided
            if owner_id is not None:
                product = app.db.execute('''
                    SELECT owner_id FROM Products
                    WHERE product_id = :product_id
                ''', product_id=product_id)

                if not product or product[0][0] != owner_id:
                    return False, "You don't have permission to delete this product"

            # Check if product is in any orders
            orders = app.db.execute('''
                SELECT COUNT(*) FROM Orders_Products
                WHERE product_id = :product_id
            ''', product_id=product_id)

            if orders[0][0] > 0:
                return False, "Cannot delete product with associated orders"

            # Delete product from cart
            app.db.execute('''
                DELETE FROM Cart_Products
                WHERE product_id = :product_id
            ''', product_id=product_id)

            # Delete product from inventory
            app.db.execute('''
                DELETE FROM Inventory
                WHERE product_id = :product_id
            ''', product_id=product_id)

            # Delete product reviews
            app.db.execute('''
                DELETE FROM Reviews_Feedbacks
                WHERE product_id = :product_id
            ''', product_id=product_id)

            # Delete the product
            app.db.execute('''
                DELETE FROM Products
                WHERE product_id = :product_id
            ''', product_id=product_id)

            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_featured_products(limit=6):
        """Get featured products (highest rated or most reviewed)"""
        rows = app.db.execute('''
            SELECT p.product_id, p.category_id, p.product_name, p.description, 
                   p.image, p.owner_id, p.created_at, p.updated_at, 
                   c.category_name, CONCAT(a.first_name, ' ', a.last_name) AS owner_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.review_id) as review_count
            FROM Products p
            JOIN Products_Categories c ON p.category_id = c.category_id
            JOIN Accounts a ON p.owner_id = a.user_id
            LEFT JOIN Reviews_Feedbacks r ON p.product_id = r.product_id
            GROUP BY p.product_id, c.category_name, a.first_name, a.last_name
            ORDER BY avg_rating DESC, review_count DESC
            LIMIT :limit
        ''', limit=limit)

        return [Product(*row) for row in rows]

    @staticmethod
    def get_available_products():
        """Get products that are available in inventory"""
        rows = app.db.execute('''
            SELECT DISTINCT p.product_id, p.category_id, p.product_name, p.description, 
                   p.image, p.owner_id, p.created_at, p.updated_at, 
                   c.category_name, CONCAT(a.first_name, ' ', a.last_name) AS owner_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.review_id) as review_count
            FROM Products p
            JOIN Products_Categories c ON p.category_id = c.category_id
            JOIN Accounts a ON p.owner_id = a.user_id
            JOIN Inventory i ON p.product_id = i.product_id
            LEFT JOIN Reviews_Feedbacks r ON p.product_id = r.product_id
            WHERE i.quantity > 0
            GROUP BY p.product_id, c.category_name, a.first_name, a.last_name
            ORDER BY p.product_name
        ''')

        return [Product(*row) for row in rows]

    def get_inventory_items(self):
        """Get inventory items for this product"""
        from .inventory import Inventory
        return Inventory.get_sellers_for_product(self.id)

    def get_reviews(self):
        """Get reviews for this product"""
        from .review import Review
        return Review.get_product_review(self.id)

    def to_dict(self):
        """Convert product to dictionary"""
        inventory_items = []
        try:
            inventory_items = [inv.to_dict() for inv in self.get_inventory_items()]
        except Exception as e:
            print(f"Error fetching inventory for product {self.id}: {str(e)}")
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'name': self.name,
            'description': self.description,
            'image': self.image,
            'owner_id': self.owner_id,
            'owner_name': self.owner_name,
            'avg_rating': float(self.avg_rating) if self.avg_rating else 0,
            'review_count': self.review_count or 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'inventory': inventory_items
        }