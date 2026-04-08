from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas import schemas
from app.database.database import get_db
from app.model import model 
from app.document import document
router = APIRouter(prefix="/document",tags=["Document"])

@router.post("/upload",response_model=schemas.DocumentResponse)
async def upload_document(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    allowed_extensions = (".pdf", ".txt", ".csv", ".xlsx", ".xls", ".doc", ".docx", ".png", ".jpg", ".jpeg")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Unsupported file format")
        
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save the file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Save to SQLite
    new_doc = models.Document(
        filename=file.filename,
        user_id=current_user.id,
        status="processing"
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    try:
        # Process and save to ChromaDB
        num_chunks = process_and_embed_document(file_path, current_user.id)
        
        # Update status
        new_doc.status = "completed"
        db.commit()
        
        return {
            "message": f"Successfully uploaded and indexed", 
            "filename": file.filename,
            "chunks": num_chunks
        }
    except Exception as e:
        new_doc.status = f"failed: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")