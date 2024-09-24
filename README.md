# ScholarFlow - Made by Ajay Avasi, Arjun Gilhotra, Sahas Maduri
🎓 Inspiration
Entering our junior year, we realized we were unprepared for college applications. Over the last couple of weeks, we scrambled to find professors to work with to possibly land a research internship. There was one big problem though: we had no idea which professors we wanted to contact. This naturally led us to our newest product, "ScholarFlow". With our website, we assure you that finding professors and research papers that interest you will feel effortless, like flowing down a stream. 🌊

💡 What it Does
Similar to the popular dating app Tinder, we provide you with hundreds of research articles and papers, and you choose whether to approve or discard them by swiping right or left. Our recommendation system will then provide you with what we think might interest you. Additionally, you can talk to our chatbot, "Scholar Chat" 🤖. This chatbot allows you to ask specific questions like, "What are some Machine Learning papers?". Both the recommendation system and chatbot will provide you with links, names, colleges, and descriptions, giving you all the information you need to find your next internship and accelerate your career 🚀.

🛠️ How We Built It
While half of our team worked on REST API endpoints and front-end development, the rest worked on scraping Google Scholar for data on published papers. The website was built using HTML/CSS/JS with the Bulma CSS framework. We used Flask to create API endpoints for JSON-based communication between the server and the front end.

To process the data, we used sentence-transformers from HuggingFace to vectorize everything. Afterward, we performed calculations on the vectors to find the optimal vector for the highest accuracy in recommendations. MongoDB Vector Search was key to retrieving documents at lightning speed, which helped provide context to the Cerebras Llama3 LLM 🧠. The query is summarized, keywords are extracted, and top-k similar documents are retrieved from the vector database. We then combined context with some prompt engineering to create a seamless and human-like interaction with the LLM.

🚧 Challenges We Ran Into
The biggest challenge we faced was gathering data from Google Scholar due to their servers blocking requests from automated bots 🤖⛔. It took several hours of debugging and thinking to obtain a large enough dataset. Another challenge was collaboration – LiveShare from Visual Studio Code would frequently disconnect, making teamwork difficult. Many tasks were dependent on one another, so we often had to wait for one person to finish before another could begin. However, we overcame these obstacles and created something we're truly proud of! 💪

🏆 Accomplishments That We're Proud Of
We’re most proud of the chatbot, both in its front and backend implementations. What amazed us the most was how accurately the Llama3 model understood context and delivered relevant answers. We could even ask follow-up questions and receive blazing-fast responses, thanks to Cerebras 🏅.

📚 What We Learned
The most important lesson was learning how to work together as a team. Despite the challenges, we pushed each other to the limit to reach our goal and finish the project. On the technical side, we learned how to use Bulma and Vector Search from MongoDB. But the most valuable lesson was using Cerebras – the speed and accuracy were simply incredible! Cerebras is the future of LLMs, and we can't wait to use it in future projects. 🚀

🔮 What's Next for ScholarFlow
Currently, our data is limited. In the future, we’re excited to expand our dataset by collaborating with Google Scholar to gain even more information for our platform. Additionally, we have plans to develop an iOS app 📱 so people can discover new professors on the go!
