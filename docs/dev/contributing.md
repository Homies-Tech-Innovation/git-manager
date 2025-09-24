### Project Structure & Tools

Our project uses a **monorepo** structure, with all our code living in a single GitHub repository. We’ll be using a shared **Google Colab notebook** for development and training, with our datasets and models stored in a shared **Google Drive** folder. Always check Google Drive first for the latest versions of files.

---

### Your Workflow

Contributing to our project is straightforward and follows these steps:

1.  **Check for Tasks:** Look at our **GitHub Projects board** to see what tasks are assigned to you. Each task will have a title, description with instructions, and labels.
2.  **Get the Data & Models:** Access the latest dataset and model files from the shared Google Drive. Don't work on older versions.
3.  **Fork the Colab Notebook:** Make a copy of our main Google Colab notebook. This ensures you're working independently without affecting the original.
4.  **Work and Train:** Use your forked notebook to complete the assigned task, such as cleaning data or training a model.
5.  **Save Your Work:**
    - **Models:** When you save your trained model, **do not overwrite** the existing version in Google Drive. Instead, save it as a new file following this convention: `[model_name]_[your_name]_[version_number]`. For example, if the latest model is `summarization_model_v12`, your version would be `summarization_model_devA_v13`.
    - **Processed Data:** Similarly, when saving processed data, create a **new file** with your name and the version number.
6.  **Submit for Review:** Once your work is complete, upload the new model and/or processed data files to the designated folders in Google Drive. Then, move your task on the **GitHub Projects board** to the **"Review"** column and tag the designated reviewer.
7.  **Final Approval:** A model is not considered the "latest" until it has been reviewed and approved. Once approved, the reviewer will move the task to the "Done" column and let you know on Discord that your work has been accepted.

---

### Important Rules

- **Never delete or modify a current file in Google Drive.** Always create a new version with your changes. This is for tracking and safety.
- **Old versions of models and datasets will be deleted occasionally** to save space, but a read-only backup will be kept.
- **Stick to the naming conventions** for models and processed data. This is crucial for keeping our files organized.
- **Communicate dependencies.** If your task depends on another task being completed first, make sure to note this on the GitHub Projects board.
- **Review existing files** before starting a new task to avoid doing work that someone else has already done.
