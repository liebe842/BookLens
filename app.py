import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json
from urllib.parse import quote

# Google Books API 설정
GOOGLE_BOOKS_API_KEY = st.secrets["GOOGLE_BOOKS_API_KEY"]
GOOGLE_BOOKS_BASE_URL = "https://www.googleapis.com/books/v1/volumes"

def fetch_books_data(query, max_results=5):
    """Google Books API를 통해 도서 정보를 가져오는 함수"""
    try:
        # URL 인코딩 전에 검색어 정리
        query = query.replace('/', ' ').strip()
        encoded_query = quote(query)
        
        params = {
            'q': encoded_query,
            'key': GOOGLE_BOOKS_API_KEY,
            'maxResults': max_results,
            'langRestrict': 'ko'
        }
        
        response = requests.get(GOOGLE_BOOKS_BASE_URL, params=params)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        return response.json()
    except requests.RequestException as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return None

def process_book_data(book_item):
    """API 응답에서 필요한 도서 정보만 추출하는 함수"""
    volume_info = book_item.get('volumeInfo', {})
    
    return {
        'title': volume_info.get('title', '제목 없음'),
        'authors': volume_info.get('authors', ['작자 미상']),
        'publisher': volume_info.get('publisher', '출판사 정보 없음'),
        'published_date': volume_info.get('publishedDate', '날짜 정보 없음'),
        'description': volume_info.get('description', '설명 없음'),
        'categories': volume_info.get('categories', ['분류 없음']),
        'image_links': volume_info.get('imageLinks', {}).get('thumbnail', None),
        'preview_link': volume_info.get('previewLink', None)
    }

def get_book_recommendations(user_preferences):
    """사용자 선호도를 기반으로 책을 추천하는 함수"""
    # 검색어 생성 방식 수정
    search_terms = []
    
    # 장르와 주제를 하나의 검색어로 결합
    if user_preferences["genre"]:
        search_terms.append(" ".join(user_preferences["genre"]))
    if user_preferences["topics"]:
        search_terms.append(" ".join(user_preferences["topics"]))
    
    # 작가는 별도로 처리
    if user_preferences["author"]:
        search_terms.append(f"inauthor:{user_preferences['author']}")
    
    # 검색어를 공백으로 구분하여 하나의 문자열로 결합
    query = " ".join(search_terms)
    
    # 검색어가 비어있는 경우 처리
    if not query.strip():
        return []
    
    books_data = fetch_books_data(query, max_results=10)
    
    if not books_data or 'items' not in books_data:
        return []
    
    recommendations = [process_book_data(item) for item in books_data['items']]
    return recommendations

# 사용자 인터페이스 부분 수정
def display_book_recommendation(book):
    """책 추천 결과를 표시하는 함수"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if book['image_links']:
            st.image(book['image_links'], width=150)
        else:
            st.image("https://placeholder.com/150x200", width=150)
    
    with col2:
        st.subheader(book['title'])
        st.write(f"저자: {', '.join(book['authors'])}")
        st.write(f"출판사: {book['publisher']}")
        st.write(f"출판일: {book['published_date']}")
        st.write(f"카테고리: {', '.join(book['categories'])}")
        
        if book['preview_link']:
            st.markdown(f"[도서 미리보기]({book['preview_link']})")
        
        with st.expander("도서 설명 보기"):
            st.write(book['description'])

def get_user_preferences():
    st.header("도서 추천을 위한 정보를 입력해주세요")
    
    # 사용자 선호도 입력 받기
    genre = st.multiselect(
        "선호하는 장르를 선택해주세요",
        ["소설", "시/에세이", "자기계발", "경제/경영", "인문학", "과학"]
    )
    
    favorite_author = st.text_input("좋아하는 작가가 있다면 입력해주세요")
    
    recent_book = st.text_input("최근에 읽은 책을 입력해주세요")
    
    preferred_topics = st.multiselect(
        "관심 있는 주제를 선택해주세요",
        ["로맨스", "추리", "판타지", "역사", "심리", "철학", "기술", "예술"]
    )
    
    return {
        "genre": genre,
        "author": favorite_author,
        "recent_book": recent_book,
        "topics": preferred_topics
    }

def main():
    st.title("📚 개인화 도서 추천 시스템1")
    
    # 사용자 선호도 입력 받기
    user_preferences = get_user_preferences()  # 이전 코드와 동일
    
    if st.button("도서 추천 받기"):
        with st.spinner('추천 도서를 검색 중입니다...'):
            recommendations = get_book_recommendations(user_preferences)
            
            if recommendations:
                st.header("추천 도서 목록")
                for book in recommendations:
                    display_book_recommendation(book)
                    
                    # 피드백 수집
                    feedback = st.selectbox(
                        "이 추천이 도움이 되었나요?",
                        ["선택해주세요", "매우 좋음", "좋음", "보통", "별로"],
                        key=f"feedback_{book['title']}"
                    )
            else:
                st.warning("추천할 만한 도서를 찾지 못했습니다. 다른 선호도를 입력해보세요.")

if __name__ == "__main__":
    main() 
