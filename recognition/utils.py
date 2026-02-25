def comparar_con_encodings(encoding, encodings, nombres, umbral=0.6):
    if not encodings:
        return None
    import face_recognition
    distancias = face_recognition.face_distance(encodings, encoding)
    min_dist = min(distancias)
    if min_dist < umbral:
        idx = list(distancias).index(min_dist)
        return nombres[idx]
    return None