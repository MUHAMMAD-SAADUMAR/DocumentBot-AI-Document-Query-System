from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.runnables import RunnablePassthrough

class Chain:
        
    
    def __init__(self, model_name="llama3.2"):
        
        self.OPENAI_API_KEY = "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"  # <<== YOUR KEY
        self.OPENAI_API_BASE = "https://openrouter.ai/api/v1"  # OpenRouter Base URL
        self.llm  = ChatOpenAI(
            openai_api_key=self.OPENAI_API_KEY,
            openai_api_base=self.OPENAI_API_BASE,
            model="openai/gpt-3.5-turbo",
            temperature=0.3,
        )
        self.model_name = model_name

        self.query_prompt = PromptTemplate(
            input_variables=["question"],
            template="""
                You are an advanced AI that helps users by generating diverse versions of their input questions.
                The goal is to generate multiple distinct and nuanced questions that will help improve the results of a similarity search. 
                Please create five different versions of the following user question, which vary in phrasing, structure, and scope:

                User Question: {question}

                Versions of the question:
                1. 
                2. 
                3. 
                4. 
                5.
            """
        )
        
        self.answer_prompt_template = """
            Answer the question based ONLY on the following context:
            {context}
            Question: {question}
        """
        self.answer_prompt = ChatPromptTemplate.from_template(self.answer_prompt_template)

    def build_chain(self, vector_db):
        if not vector_db:
            return None
            
        retriever = MultiQueryRetriever.from_llm(
            retriever=vector_db.as_retriever(),
            llm=self.llm,
            prompt=self.query_prompt
        )

        chain = (
            {
                "context": retriever,
                "question": RunnablePassthrough()
            }
            | self.answer_prompt
            | self.llm
            | StrOutputParser()
        )

        return chain