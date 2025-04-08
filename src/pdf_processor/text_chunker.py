"""
Module for chunking text for LLM processing.
"""
import logging

# Configure logging
logger = logging.getLogger(__name__)

def chunk_text(text, chunk_size=1000, overlap=100, respect_paragraphs=True):
    """
    Split text into chunks for processing by LLM with improved handling of text boundaries.
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Maximum size of each chunk
        overlap (int): Overlap between chunks in characters
        respect_paragraphs (bool): Try to keep paragraphs together when possible
        
    Returns:
        list: List of dictionaries containing:
            - 'content': The text chunk
            - 'index': Chunk index
            - 'start_char': Starting character position in original text
            - 'end_char': Ending character position in original text
    """
    if not text:
        return []
    
    logger.info(f"Chunking text of {len(text)} characters (chunk_size={chunk_size}, overlap={overlap})")
    chunks = []
    
    # If respecting paragraphs, split by paragraph first
    if respect_paragraphs:
        # Split text by paragraph breaks (double newlines)
        paragraphs = text.split('\n\n')
        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        current_chunk = ""
        current_start = 0
        start_char_pos = 0
        
        for para in paragraphs:
            # If adding this paragraph exceeds chunk_size and we already have content,
            # save the current chunk and start a new one
            if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
                end_char_pos = start_char_pos + len(current_chunk)
                chunks.append({
                    'content': current_chunk,
                    'index': len(chunks),
                    'start_char': start_char_pos,
                    'end_char': end_char_pos
                })
                
                # Calculate the overlap point
                if overlap > 0:
                    # Try to find a sentence break in the last part of the text for overlap
                    overlap_text = current_chunk[-overlap:]
                    sentence_breaks = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
                    
                    # Find the last sentence break in the overlap region
                    last_break_pos = -1
                    for break_char in sentence_breaks:
                        pos = overlap_text.rfind(break_char)
                        if pos > last_break_pos:
                            last_break_pos = pos
                    
                    # If we found a sentence break, use it for overlap
                    if last_break_pos > 0:
                        # +2 to include the sentence-ending punctuation
                        overlap_start = len(current_chunk) - overlap + last_break_pos + 2
                        current_chunk = current_chunk[overlap_start:]
                        start_char_pos = start_char_pos + overlap_start
                    else:
                        # If no sentence break, use regular overlap
                        current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                        start_char_pos = start_char_pos + (len(current_chunk) - overlap)
                else:
                    current_chunk = ""
                    start_char_pos = end_char_pos
            
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        
        # Add the last chunk if it has content
        if current_chunk:
            end_char_pos = start_char_pos + len(current_chunk)
            chunks.append({
                'content': current_chunk,
                'index': len(chunks),
                'start_char': start_char_pos,
                'end_char': end_char_pos
            })
    
    else:
        # Simpler character-based chunking with improved sentence boundary respect
        i = 0
        while i < len(text):
            # Determine end position for this chunk
            end_pos = min(i + chunk_size, len(text))
            
            # If we're not at the end of the text and not at a natural boundary,
            # try to find a sentence boundary
            if end_pos < len(text):
                # Look for sentence boundaries (., !, ?)
                sentence_end = max(
                    text.rfind('. ', i, end_pos),
                    text.rfind('! ', i, end_pos),
                    text.rfind('? ', i, end_pos),
                    text.rfind('.\n', i, end_pos),
                    text.rfind('!\n', i, end_pos),
                    text.rfind('?\n', i, end_pos)
                )
                
                # If we found a sentence boundary, use it
                if sentence_end > i:
                    # +2 to include the sentence-ending punctuation and space
                    end_pos = sentence_end + 2
            
            # Create the chunk
            chunk_text = text[i:end_pos]
            chunks.append({
                'content': chunk_text,
                'index': len(chunks),
                'start_char': i,
                'end_char': end_pos
            })
            
            # Move to the next chunk, accounting for overlap
            i = end_pos - overlap if overlap < (end_pos - i) else i + 1
    
    logger.info(f"Created {len(chunks)} chunks from text")
    return chunks