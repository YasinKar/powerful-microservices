import uuid
import random
from typing import List

import click
import factory
from faker import Faker
from sqlmodel import select

from models.category import Brand, Category
from models.product import Product, ProductImage
from core.db import Session, engine


fake = Faker()


class CategoryFactory(factory.Factory):
    class Meta:
        model = Category

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.LazyAttribute(lambda _: fake.unique.word().capitalize() + " Category")
    is_active = True


class BrandFactory(factory.Factory):
    class Meta:
        model = Brand

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.LazyAttribute(lambda _: fake.unique.company())
    is_active = True


class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.LazyAttribute(lambda _: fake.word())
    description = factory.LazyAttribute(lambda _: fake.paragraph())
    stock = factory.LazyAttribute(lambda _: random.randint(0, 100))
    category = factory.SubFactory(CategoryFactory)
    brand = factory.SubFactory(BrandFactory)
    is_active = True
    rating = factory.LazyAttribute(lambda _: round(random.uniform(0.0, 5.0), 1))


class ProductImageFactory(factory.Factory):
    class Meta:
        model = ProductImage

    id = factory.LazyFunction(uuid.uuid4)
    product = factory.SubFactory(ProductFactory)
    image_url = factory.LazyAttribute(lambda _: fake.image_url())
    alt_text = factory.LazyAttribute(lambda _: fake.sentence(nb_words=5))


def seed_database(num_categories=5, num_brands=5, num_products=20, images_per_product=3):
    with Session(engine) as session:
        existing_categories = session.exec(select(Category)).all()
        if existing_categories:
            print("Database already seeded with categories. Skipping.")
            return

        # Create categories
        categories: List[Category] = CategoryFactory.build_batch(num_categories)
        session.add_all(categories)
        session.commit()

        # Create brands
        brands: List[Brand] = BrandFactory.build_batch(num_brands)
        session.add_all(brands)
        session.commit()

        # Create products
        for _ in range(num_products):
            product = ProductFactory(
                category=random.choice(categories),
                brand=random.choice(brands),
            )
            session.add(product)
            session.commit()

            # Create images for the product
            images: List[ProductImage] = []
            for _ in range(images_per_product):
                image = ProductImageFactory(product=product)
                images.append(image)
            session.add_all(images)
            session.commit()

        print(f"Seeded {num_categories} categories, {num_brands} brands, {num_products} products, and associated images.")


# CLI command
@click.command()
def seed():
    seed_database()


if __name__ == "__main__":
    seed()