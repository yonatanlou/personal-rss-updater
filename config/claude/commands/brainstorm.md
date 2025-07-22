Ask me one question at a time so we can develop a thorough, step-by-step spec for this idea. Each question should build on my previous answers, and our end goal is to have a detailed specification I can hand off to a developer. Let’s do this iteratively and dig into every relevant detail. Remember, only one question at a time.

Once we are done, save the spec as spec.md

Ask if the user wants to create a git repo on github. if so, commit the spec.md to git and push it to the newly created git repo.

Here’s the idea:
A robust Python program that runs once a day, given a list of blogs, check if there are new posts on those blogs. if there are new posts, send email notifications for this new content.
Those blogs are blogs without and RSS features like the website https://simplystatistics.org/.
I want that the infra will be written in modern python, and it will be easy to handle dependecies etc.
I want to be able to run it both locally and both from github actions.
