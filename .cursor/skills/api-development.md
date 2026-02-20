---
name: api-development
description: Skills for building REST APIs with FastAPI
---

# API Development Skills

## FastAPI Best Practices

When building APIs:

1. **Use Pydantic models** for request/response validation
2. **Implement proper error handling** with HTTPException
3. **Add OpenAPI documentation** with descriptions
4. **Use dependency injection** for shared resources
5. **Implement async endpoints** for I/O operations

## Example Structure

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI(title="My API", version="1.0.0")

class ItemCreate(BaseModel):
    name: str
    price: float

@app.post("/items/", response_model=Item)
async def create_item(item: ItemCreate):
    # Implementation
    pass
```

## Testing APIs

- Use TestClient from fastapi.testing
- Test both success and error cases
- Verify response schemas
