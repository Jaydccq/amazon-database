INSERT INTO Products_Categories (category_id, category_name) VALUES
(1, 'Desserts'),
(2, 'Drinks'),
(3, 'Soda'),
(4, 'Snacks'),
(5, 'Bakery')
ON CONFLICT (category_id) DO NOTHING;

INSERT INTO Products (product_id
, category_id, product_name, description, image, owner_id) VALUES
(1, 1, 'Vanilla Ice Cream', 'Classic vanilla flavor ice cream.', 'https://example.com/vanilla.jpg', 1),
(2, 1, 'Chocolate Ice Cream', 'Rich chocolate ice cream.', 'https://example.com/chocolate.jpg', 1),
(3, 2, 'Strawberry Smoothie', 'Fresh strawberry drink.', 'https://example.com/strawberry.jpg', 2),
(4, 2, 'Orange Juice', '100% pure orange juice.', 'https://example.com/orange.jpg', 2),
(5, 3, 'Coca Cola Pack', '12-pack classic Coca-Cola.', 'https://example.com/coke.jpg', 3),
(6, 3, 'Pepsi Can', '330ml single can of Pepsi.', 'https://example.com/pepsi.jpg', 3),
(7, 4, 'Cookies', 'Homemade chocolate chip cookies.', 'https://example.com/cookies.jpg', 1),
(8, 4, 'Brownie', 'Fudge brownie square.', 'https://example.com/brownie.jpg', 1),
(9, 5, 'Apple Pie', 'Slice of warm apple pie.', 'https://example.com/applepie.jpg', 2),
(10, 5, 'Cheesecake', 'New York-style cheesecake.', 'https://example.com/cheesecake.jpg', 2)
ON CONFLICT (product_id) DO NOTHING;

INSERT INTO Inventory (product_id, seller_id, quantity, unit_price) VALUES
(1, 1, 20, 3.99),
(2, 1, 15, 4.49),
(3, 2, 10, 5.25),
(4, 2, 12, 3.75),
(5, 3, 18, 6.00),
(6, 3, 30, 2.50),
(7, 1, 25, 2.99),
(8, 1, 10, 3.50),
(9, 2, 8, 5.99),
(10, 2, 6, 6.49)
ON CONFLICT (seller_id, product_id) DO NOTHING;

