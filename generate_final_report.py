from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def add_section_heading(document, title):
    document.add_heading(title, level=1)


document = Document()
document.styles['Normal'].font.name = 'Calibri'
document.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri')

paragraph = document.add_paragraph()
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = paragraph.add_run('MLOps Assignment: Heart Disease Prediction Pipeline')
run.bold = True
run.font.size = 22

document.add_paragraph('Student/Team Project Report')
document.add_paragraph('Academic MLOps Assignment, 2026')
document.add_paragraph('Repository: https://github.com/sanjaybet/mlops_assignment01')
document.add_paragraph('')

add_section_heading(document, '1. Introduction and objective')
document.add_paragraph('This report documents the design, implementation, and validation of a reproducible machine learning solution for heart disease prediction using the UCI Cleveland Heart Disease dataset. The project follows the core principles of Machine Learning Operations (MLOps) by integrating data ingestion, cleaning, feature engineering, experimentation, model deployment, testing, automation, and containerization into a single end-to-end workflow.')
document.add_paragraph('The objective was to build a production-style machine learning pipeline that could be run from a clean environment, validated through automated tests, and exposed via a prediction API. The project emphasizes reproducibility, traceability, automated deployment readiness, and operational observability using modern tools such as Python, scikit-learn, MLflow, FastAPI, Docker, Kubernetes manifests, and GitHub Actions.')
document.add_paragraph('The assignment required not only the creation of a functioning model, but also the ability to package it for service deployment and CI validation. This is why the solution contains both a training pipeline and a serving layer, and why production-readiness checks were incorporated into the workflow.')
document.add_page_break()

add_section_heading(document, '2. Environment and setup')
document.add_paragraph('The project was implemented in a dedicated Python virtual environment to ensure dependency isolation and repeatability. The environment includes the core data science stack, model training libraries, FastAPI, MLflow, and testing dependencies. A local setup requires Python 3.12, pip, Docker, and Git. The project dependency list is captured in requirements.txt so that the environment can be reconstructed cleanly from a fresh machine.')
document.add_paragraph('The installation and setup commands are included in the project README. The virtual environment was activated before running the project scripts, and a clean installation workflow was used to avoid manual package discrepancies across local or CI environments. This approach follows the reproducibility requirement in the assignment, which emphasizes that all scripts should be executable from a clean setup using the requirements file.')
document.add_paragraph('The environment configuration also addressed an MLflow compatibility issue caused by a setuptools version conflict. This was resolved by pinning setuptools<81 in the requirements file. This demonstrates a practical MLOps consideration: package compatibility and environment stability are critical for reliable training and deployment.')
document.add_paragraph('The setup therefore covers both developer ergonomics and deployment consistency. This is a key requirement for production-like systems, where environment drift is a major source of failure.')
document.add_page_break()

add_section_heading(document, '3. Data acquisition and validation')
document.add_paragraph('The first major stage was data acquisition. The project uses the official UCI Heart Disease dataset, which is downloaded from the public source archive and stored under the raw-data directory. This ensures that the training dataset is reproducible and traceable, rather than relying on ad hoc local copies or manually edited files.')
document.add_paragraph('The download workflow is implemented in the data acquisition script. It obtains the dataset archive, extracts the Cleveland records, validates the expected schema, and confirms that the dataset has the necessary rows and columns. The dataset checks ensure the pipeline fails early if the raw source is incomplete or malformed. This principle is consistent with production systems, which must gracefully detect invalid upstream data before training begins.')
document.add_paragraph('The raw dataset was verified to contain the expected number of rows and the standard feature columns used in the heart disease problem. This validation is important because downstream modelling decisions depend on a correct and consistent dataset schema. Without schema validation, a single missing or renamed feature can cause silent model errors and unreliable outputs.')
document.add_paragraph('This stage also satisfies the deliverable requirement for a clean dataset and download script instructions. The dataset, raw data location, and instructions for running the acquisition process are all included in the repository and documentation.')
document.add_page_break()

add_section_heading(document, '4. Exploratory data analysis and preprocessing')
document.add_paragraph('After data acquisition, the project performs exploratory data analysis and preprocessing. The analysis pipeline checks the schema, validates target values, and maps the original multi-class disease labels to a binary classification target. Specifically, the original target levels 0 to 4 are mapped so that 0 is classified as no disease and values from 1 to 4 are treated as disease present.')
document.add_paragraph('This binary mapping is central to the assignment because the objective is a binary prediction problem. The cleaned dataset is then saved in the processed-data folder for downstream use by the training scripts. This conversion ensures the classification task aligns with the intended predictive objective and avoids ambiguity in model interpretation.')
document.add_paragraph('The project also produces a range of EDA visualizations, including feature histograms, class balance plots, and correlation heatmaps. These diagnostic plots help confirm feature distribution quality, detect imbalance or anomalies, and support modelling decisions. In a production workflow, this stage is crucial because it enables early identification of data quality issues before expensive model training takes place.')
document.add_paragraph('The implementation uses preprocessing pipelines designed with leakage awareness. Numeric features are imputed and scaled, while categorical features are imputed and one-hot encoded. This design is preferred over manual feature preprocessing because it keeps the transformation logic inside the training pipeline and ensures consistent behaviour in both training and inference.')
document.add_page_break()

add_section_heading(document, '5. Model development and evaluation')
document.add_paragraph('The model development stage compares multiple candidate classifiers before selecting a final champion. The project evaluates Logistic Regression and Random Forest classifiers using a stratified cross-validation approach and a holdout validation set. This is a principled model selection strategy because it reduces the risk of overfitting and gives a realistic estimate of generalization performance.')
document.add_paragraph('The training script builds a preprocessing pipeline for each candidate model. The pipeline includes imputation, scaling, encoding, and the classifier itself. This ensures that all transformations are learned only on training data during the cross-validation loops, which prevents data leakage from the validation folds into the training process.')
document.add_paragraph('The model selection metric used for comparison is the cross-validated ROC-AUC score, which is appropriate for binary classification tasks and reflects the ability of the classifier to distinguish between classes. After comparing the candidate models, the project selects the champion based on the best validation performance and then evaluates that model on the holdout test set. This is a standard and reliable approach in applied ML workflows.')
document.add_paragraph('The project also saves confusion matrices and ROC curves so that the performance of each model can be inspected visually. These artifacts were included in the screenshot folder and used to support the reporting requirement. They provide evidence that the model not only classifies samples, but does so with a useful discrimination threshold and interpretable error patterns.')
document.add_page_break()

add_section_heading(document, '6. MLflow experiment tracking')
document.add_paragraph('MLflow is a core component of the project and is used to record experiment metadata, training metrics, and model artifacts. The training workflow logs the experiment name, hyperparameters, data preparation choices, validation scores, plots, and the final serialized model. This is essential for establishing a reproducible machine learning process, where every run can be traced and compared.')
document.add_paragraph('In this project, the MLflow experiment tracks the candidate classifiers and records the relevant metrics for each run. By logging cross-validation results, the project preserves the evidence used for model selection. This is particularly important in MLOps because it creates a traceable model history rather than leaving performance results only in an ad hoc console output.')
document.add_paragraph('The experiment tracking layer also supports governance and collaboration. If multiple people are working on the same model, MLflow allows them to review parameters, compare runs, and identify the exact configuration that produced the best result. This is a recurring requirement in production MLOps pipelines, where model lineage and auditability matter.')
document.add_paragraph('The final artifact is a saved model pipeline that can be reloaded for inference, enabling a clear distinction between experimentation and deployment. This separation is a key practice in robust machine learning systems.')
document.add_page_break()

add_section_heading(document, '7. Deployment of the prediction service')
document.add_paragraph('Once the model was trained and validated, it was exposed through a FastAPI application. The prediction service receives patient information in JSON format, loads the serialized model artifact, and returns the disease prediction together with probability scores for both disease and no-disease classes. This API layer is the operational entry point for downstream users and stakeholders.')
document.add_paragraph('The API implementation includes health-check endpoints and an inference endpoint. This design is useful for both local testing and deployment monitoring because it allows the service to be easily validated by a lightweight HTTP request. The service is designed to be stateless and portable, which makes it suitable for containerized deployment.')
document.add_paragraph('The project includes local access instructions in the README and has been verified through smoke tests. This satisfies the deployment requirement that the model be served correctly in an isolated environment and that a working API can be exercised without a full production cluster. It also helps satisfy the assignment requirement for access instructions when a public URL is not available.')
document.add_paragraph('When a public URL is not available, local instructions remain valid because they demonstrate how the application can be run and tested in a production-like environment. For academic submissions, this is usually accepted if the service has been proven to work locally and the instructions are clearly provided.')
document.add_page_break()

add_section_heading(document, '8. CI/CD and Dockerization')
document.add_paragraph('The project uses GitHub Actions for automated validation. The workflow checks out the repository, installs the requirements, runs linting, executes tests, and then triggers the data processing and training pipeline. This is a standard continuous integration pattern and helps enforce quality standards on every change to the repository.')
document.add_paragraph('The pipeline is designed to fail clearly if any component of the workflow fails. This is important because production systems should not silently accept invalid code or broken environment assumptions. In the project, the workflow therefore acts as a guardrail by running the tests and model training automatically before the code is considered acceptable.')
document.add_paragraph('The application is also containerized using Docker. The Dockerfile creates a slim Python environment, installs the project requirements, copies the source code, and starts the FastAPI server. This allows the project to be run consistently across local development, CI, and deployment environments. The container architecture is an essential MLOps practice because it minimizes environment drift and simplifies portability.')
document.add_paragraph('Together, the GitHub Actions workflow and Docker configuration ensure both automation and reproducibility. This covers the assignment requirement for pipeline validation, deployment packaging, and environment consistency.')
document.add_page_break()

add_section_heading(document, '9. Production-readiness and compliance check')
document.add_paragraph('The project was reviewed against the production-readiness requirements in the assignment. The first requirement is that all scripts should run from a clean setup using the requirements file; this is satisfied by the project configuration and environment instructions. The second requirement is that the model should serve correctly in an isolated environment; this is demonstrated by the Docker configuration and the API validation steps. The third requirement is that the pipeline should fail on code or test errors and provide clear logs; this is satisfied by the GitHub Actions workflow and the test suite, which exit non-zero on failure.')
document.add_paragraph('In addition, the assignment requires the project to include the relevant repository artifacts, such as source code, training scripts, deployment manifests, tests, data artifacts, screenshots, and a final written report. These are all present in the project workspace or included as part of the documented setup. The project therefore satisfies the main functional and operational requirements for a complete MLOps assignment submission.')
document.add_paragraph('The only item that may still require a manual demonstration is the short video recording of the overall pipeline. If the instructor expects a recorded walkthrough, it should be prepared and attached separately as a short demonstration clip. The repository itself contains the code, tests, manifests, and documentation needed to support the explanation. This is the final practical artifact required outside of the repository files.')
document.add_paragraph('The work therefore demonstrates both technical completeness and demonstration readiness. It is aligned with the assignment guidelines and provides the evidence needed for code review, deployment validation, and reporting.')
document.add_page_break()

add_section_heading(document, '10. Deliverables checklist')
for item in [
    'GitHub repository with source code and model artifacts',
    'Dockerfile and dependency file',
    'Dataset download and preprocessing scripts',
    'EDA, training, and inference scripts',
    'Unit tests under tests/',
    'GitHub Actions workflow YAML',
    'Deployment manifests for Kubernetes',
    'Screenshot folder with visual outputs',
    'Final written report in Word/PDF format',
    'Local access instructions or public API URL',
    'Short demonstration video (if required by instructor)',
]:
    document.add_paragraph(f'• {item}')

document.add_paragraph('')
document.add_paragraph('Conclusion: The project was implemented and validated as a complete MLOps pipeline for heart disease prediction. It covers data acquisition, cleansing, experimentation, deployment, automation, and reporting in a way that aligns with the assignment specification and production-readiness expectations.')

document.save('Final_Report.docx')
print('Created Final_Report.docx')
