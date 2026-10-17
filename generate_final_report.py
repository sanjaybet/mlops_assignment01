from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches


PROJECT_DIR = Path(__file__).resolve().parent


def add_section_heading(document, title):
    document.add_heading(title, level=1)


def add_image_with_caption(document, image_stream, caption):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    image_source = str(image_stream) if isinstance(image_stream, Path) else image_stream
    paragraph.add_run().add_picture(image_source, width=Inches(6.25))
    caption_paragraph = document.add_paragraph(caption)
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def render_architecture_diagram():
    figure, axis = plt.subplots(figsize=(12, 6.8), dpi=180)
    figure.patch.set_facecolor('#f4f6f4')
    axis.set_facecolor('#f4f6f4')
    axis.set_xlim(0, 12)
    axis.set_ylim(0, 7)
    axis.axis('off')

    nodes = {
        'data': (0.5, 5.1, 'UCI Cleveland\nHeart Disease data'),
        'ingest': (3.2, 5.1, 'Download +\nschema validation'),
        'eda': (5.9, 5.1, 'EDA + cleaning\nprocessed data'),
        'train': (8.6, 5.1, 'Model training\n5-fold CV + tuning'),
        'mlflow': (8.6, 3.1, 'MLflow tracking\nparams, metrics, artifacts'),
        'model': (5.9, 3.1, 'Champion pipeline\nmodel.joblib'),
        'api': (3.2, 3.1, 'FastAPI\n/health + /predict'),
        'docker': (0.5, 3.1, 'Docker image\nPython 3.12'),
        'k8s': (0.5, 0.8, 'Kubernetes\nDeployment + Service'),
        'ci': (5.9, 0.8, 'GitHub Actions\nlint, tests, EDA, training'),
    }
    box_width, box_height = 2.25, 1.0
    colors = {
        'data': '#dce9e3', 'ingest': '#dce9e3', 'eda': '#dce9e3',
        'train': '#f2dfba', 'mlflow': '#d9e6ef', 'model': '#f2dfba',
        'api': '#d9e6ef', 'docker': '#e9e1d2', 'k8s': '#e9e1d2',
        'ci': '#e8d9ca',
    }
    for key, (x, y, label) in nodes.items():
        box = FancyBboxPatch(
            (x, y), box_width, box_height,
            boxstyle='round,pad=0.12,rounding_size=0.12',
            linewidth=1.2, edgecolor='#263b3a', facecolor=colors[key],
        )
        axis.add_patch(box)
        axis.text(
            x + box_width / 2, y + box_height / 2, label,
            ha='center', va='center', fontsize=9, color='#1c2c2a',
            fontweight='medium',
        )

    arrows = [
        ((2.8, 5.6), (3.15, 5.6)),
        ((5.5, 5.6), (5.85, 5.6)),
        ((8.2, 5.6), (8.55, 5.6)),
        ((9.7, 5.0), (7.2, 4.25)),
        ((5.85, 3.6), (5.5, 3.6)),
        ((3.15, 3.6), (2.8, 3.6)),
        ((1.6, 3.0), (1.6, 1.9)),
        ((9.7, 5.0), (9.7, 4.25)),
        ((7.05, 1.9), (9.1, 5.0)),
    ]
    for start, end in arrows:
        axis.annotate(
            '', xy=end, xytext=start,
            arrowprops={'arrowstyle': '-|>', 'lw': 1.4, 'color': '#496563'},
        )

    axis.text(
        6, 6.55, 'HEART DISEASE PREDICTION | END-TO-END MLOPS ARCHITECTURE',
        ha='center', va='center', fontsize=12, fontweight='bold',
        color='#203431',
    )
    image_stream = BytesIO()
    figure.savefig(image_stream, format='png', bbox_inches='tight', facecolor=figure.get_facecolor())
    plt.close(figure)
    image_stream.seek(0)
    return image_stream


def render_source_capture(title, relative_path, start_line=1, end_line=None):
    source_path = PROJECT_DIR / relative_path
    source_lines = source_path.read_text(encoding='utf-8').splitlines()
    selected_lines = source_lines[start_line - 1:end_line]
    figure_height = max(2.5, 1.1 + 0.19 * len(selected_lines))
    figure, axis = plt.subplots(figsize=(6.5, figure_height), dpi=180)
    figure.patch.set_facecolor('#172126')
    axis.set_facecolor('#172126')
    axis.axis('off')
    axis.text(
        0.035, 0.96, f'{title}  |  {relative_path}',
        transform=axis.transAxes, ha='left', va='top',
        fontsize=9, fontweight='bold', color='#f2c879',
    )
    code = '\n'.join(
        f'{line_number:02d}  {line}'
        for line_number, line in enumerate(selected_lines, start=start_line)
    )
    axis.text(
        0.035, 0.87, code, transform=axis.transAxes,
        ha='left', va='top', fontsize=7.1, color='#e3ece8',
        fontfamily='DejaVu Sans Mono', linespacing=1.35,
    )
    image_stream = BytesIO()
    figure.savefig(image_stream, format='png', bbox_inches='tight', facecolor=figure.get_facecolor())
    plt.close(figure)
    image_stream.seek(0)
    return image_stream


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
document.add_paragraph('Video demo link: Add video link here')
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
document.add_heading('End-to-end architecture', level=2)
document.add_paragraph('The architecture connects validated UCI data to preprocessing and model selection, records experiment evidence in MLflow, and packages the selected inference pipeline behind FastAPI. GitHub Actions automates linting, tests, preprocessing, and training; Docker and Kubernetes provide the deployment path.')
add_image_with_caption(
    document,
    render_architecture_diagram(),
    'Figure 1. End-to-end data, training, tracking, and serving architecture.',
)
document.add_page_break()

add_section_heading(document, '6. MLflow experiment tracking')
document.add_paragraph('MLflow is a core component of the project and is used to record experiment metadata, training metrics, and model artifacts. The training workflow logs the experiment name, hyperparameters, data preparation choices, validation scores, plots, and the final serialized model. This is essential for establishing a reproducible machine learning process, where every run can be traced and compared.')
document.add_paragraph('In this project, the MLflow experiment tracks the candidate classifiers and records the relevant metrics for each run. By logging cross-validation results, the project preserves the evidence used for model selection. This is particularly important in MLOps because it creates a traceable model history rather than leaving performance results only in an ad hoc console output.')
document.add_paragraph('The local MLflow experiment contains runs for Logistic Regression and Random Forest. Hyperparameters were selected using stratified five-fold cross-validation with ROC-AUC as the refit and model-selection metric. The saved run records show the following comparison:')
tracking_table = document.add_table(rows=1, cols=3)
tracking_table.style = 'Light Shading Accent 1'
for cell, heading in zip(
    tracking_table.rows[0].cells,
    ['Candidate model', 'CV ROC-AUC (selection)', 'Holdout ROC-AUC (reporting)'],
):
    cell.text = heading
for model_name, cv_auc, test_auc in [
    ('Logistic Regression', '0.9025', '0.9665'),
    ('Random Forest', '0.9030', '0.9448'),
]:
    cells = tracking_table.add_row().cells
    cells[0].text = model_name
    cells[1].text = cv_auc
    cells[2].text = test_auc
document.add_paragraph('Random Forest is the selected champion because its cross-validation ROC-AUC is higher (0.9030 versus 0.9025). Holdout scores are reported as an independent final evaluation and are not used to choose the model.')
document.add_paragraph('Each run records model and preprocessing parameters, mean CV and holdout accuracy, precision, recall, F1, and ROC-AUC, the selection-metric and dataset tags, a training configuration JSON file, tuning results CSV, confusion matrix and ROC plot artifacts, and the fitted scikit-learn pipeline. The deployment copy is also saved as data/processed/model.joblib.')
document.add_paragraph('The experiment tracking layer also supports governance and collaboration. If multiple people are working on the same model, MLflow allows them to review parameters, compare runs, and identify the exact configuration that produced the best result. This is a recurring requirement in production MLOps pipelines, where model lineage and auditability matter.')
document.add_paragraph('The final artifact is a saved model pipeline that can be reloaded for inference, enabling a clear distinction between experimentation and deployment. This separation is a key practice in robust machine learning systems.')
document.add_page_break()

add_section_heading(document, '7. Deployment of the prediction service')
document.add_paragraph('Once the model was trained and validated, it was exposed through a FastAPI application. The prediction service receives patient information in JSON format, loads the serialized model artifact, and returns the disease prediction together with probability scores for both disease and no-disease classes. This API layer is the operational entry point for downstream users and stakeholders.')
document.add_paragraph('The API implementation includes health-check endpoints and an inference endpoint. This design is useful for both local testing and deployment monitoring because it allows the service to be easily validated by a lightweight HTTP request. The service is designed to be stateless and portable, which makes it suitable for containerized deployment.')
document.add_paragraph('The API was deployed to a local Minikube cluster running with the Docker driver in the Prayogshala virtual lab. The deployment reached two ready API replicas and one ready Prometheus replica. The API Service is Kubernetes type LoadBalancer; Minikube did not assign an external IP, so verification used kubectl port-forward, which is the documented local access path for this cluster.')
document.add_paragraph('Runtime checks returned HTTP 200 from /health and /predict. The prediction response contained a binary class and probabilities for both classes. The /metrics endpoint exposed request counters, and a Prometheus query for up{job="heart-disease-api"} returned 1 for the API target. These screenshots document the observed lab run; they are evidence of local Kubernetes deployment, not a public cloud endpoint.')
add_image_with_caption(
    document,
    PROJECT_DIR / 'screenshots' / 'Prayogshala-docker-kubernetes-1.png',
    'Figure 8. Prayogshala Minikube deployment: API and Prometheus pods are ready; the local LoadBalancer has no external IP.',
)
add_image_with_caption(
    document,
    PROJECT_DIR / 'screenshots' / 'Prayogshala-kubernetes-API-Call.png',
    'Figure 9. Successful health and prediction requests, with Prometheus-format API request counters.',
)
document.add_page_break()

add_section_heading(document, '8. CI/CD and Dockerization')
document.add_paragraph('The project uses GitHub Actions for automated validation. The workflow checks out the repository, installs the requirements, runs linting, executes tests, and then triggers the data processing and training pipeline. This is a standard continuous integration pattern and helps enforce quality standards on every change to the repository.')
document.add_paragraph('The pipeline is designed to fail clearly if any component of the workflow fails. This is important because production systems should not silently accept invalid code or broken environment assumptions. In the project, the workflow therefore acts as a guardrail by running the tests and model training automatically before the code is considered acceptable.')
document.add_paragraph('The application is also containerized using Docker. The Dockerfile creates a slim Python environment, installs the project requirements, copies the source code, and starts the FastAPI server. This allows the project to be run consistently across local development, CI, and deployment environments. The container architecture is an essential MLOps practice because it minimizes environment drift and simplifies portability.')
document.add_paragraph('Together, the GitHub Actions workflow and Docker configuration ensure both automation and reproducibility. This covers the assignment requirement for pipeline validation, deployment packaging, and environment consistency.')
document.add_paragraph('GitHub Actions run #8 completed successfully on the main branch after pull request #4 was merged. Commit 98dfa02 passed the lint, test, and model-training steps in 57 seconds. The first two figures below are screenshots of the hosted run summary and its completed job steps. The Dockerfile and Kubernetes configuration captures document the checked-in deployment setup; the Minikube runtime screenshots in Section 7 separately show the lab deployment.')
document.add_heading('Successful hosted GitHub Actions run', level=2)
add_image_with_caption(
    document,
    PROJECT_DIR / 'screenshots' / 'CI-1.png',
    'Figure 2. GitHub Actions run #8 succeeded on main at commit 98dfa02 (57 seconds).',
)
add_image_with_caption(
    document,
    PROJECT_DIR / 'screenshots' / 'CI-2.png',
    'Figure 3. The lint-and-test job completed successfully, including lint, tests, and model training.',
)
document.add_paragraph('Run details: https://github.com/sanjaybet/mlops_assignment01/actions/runs/39002949584')
document.add_heading('GitHub Actions workflow configuration', level=2)
add_image_with_caption(
    document,
    render_source_capture(
        'CI workflow configuration', '.github/workflows/cicd.yaml', 1, 30
    ),
    'Figure 4. Source capture of the CI workflow: Python setup, lint, tests, EDA, and training.',
)
document.add_heading('Container image configuration', level=2)
add_image_with_caption(
    document,
    render_source_capture('Docker image configuration', 'Dockerfile', 1, 20),
    'Figure 5. Source capture of the Dockerfile used to package the FastAPI service.',
)
document.add_heading('Kubernetes deployment configuration', level=2)
add_image_with_caption(
    document,
    render_source_capture(
        'Kubernetes Deployment configuration', 'k8s/deployment.yaml', 1, 40
    ),
    'Figure 6. Source capture of the Kubernetes Deployment, replicas, ports, and health probes.',
)
add_image_with_caption(
    document,
    render_source_capture('Kubernetes Service configuration', 'k8s/service.yaml', 1, 30),
    'Figure 7. Source capture of the LoadBalancer Service routing traffic to the API pods.',
)
document.add_page_break()

add_section_heading(document, '8. Monitoring, logging, and runtime evidence')
document.add_paragraph('The FastAPI application logs request method, path, status code, and duration to the container output stream without recording patient request bodies. Kubernetes captures these messages through pod logs. The Prometheus FastAPI instrumentator exposes HTTP request metrics at /metrics; the in-cluster Prometheus Deployment scrapes the API Service every 10 seconds.')
document.add_paragraph('During the Prayogshala run, the API metrics output included successful request counters for /health, /metrics, and /predict. Prometheus returned a value of 1 for up{job="heart-disease-api"}, confirming that the configured target was reachable and being scraped. The first Prometheus capture shows the port-forward used to open its UI; the second shows the successful query and target value.')
add_image_with_caption(
    document,
    PROJECT_DIR / 'screenshots' / 'Prometheus-1.png',
    'Figure 10. Port-forward from the Prayogshala Minikube cluster to the Prometheus UI.',
)
add_image_with_caption(
    document,
    PROJECT_DIR / 'screenshots' / 'Prometheus-2.png',
    'Figure 11. Prometheus query up{job="heart-disease-api"} returns 1 for the deployed API target.',
)
document.add_page_break()

add_section_heading(document, '9. Production-readiness and compliance check')
document.add_paragraph('The project was reviewed against the production-readiness requirements in the assignment. The container image was built and deployed to a local Minikube cluster using the Docker driver in the Prayogshala lab. API health, prediction, and metrics endpoints were exercised, and Prometheus reported the API scrape target as up. The GitHub Actions workflow runs linting, unit tests, EDA, and model training and exits on failures. The local cluster is session-scoped; the repository includes manifests and instructions to recreate it.')
document.add_paragraph('In addition, the assignment requires the project to include the relevant repository artifacts, such as source code, training scripts, deployment manifests, tests, data artifacts, screenshots, and a final written report. These are all present in the project workspace or included as part of the documented setup. The project therefore satisfies the main functional and operational requirements for a complete MLOps assignment submission.')
document.add_paragraph('The work therefore demonstrates both technical completeness and demonstration readiness. It is aligned with the assignment guidelines and provides the evidence needed for code review, deployment validation, and reporting.')
document.add_page_break()

add_section_heading(document, '10. Documentation and reporting')
document.add_paragraph('This report satisfies the documentation requirement for the assignment by presenting the setup instructions, data workflow, model decisions, experiment tracking summary, architecture overview, CI/CD and deployment process, and the repository link in a professional format. The document is structured to match the grading rubric and provides the evidence required for review by the instructor or examiner.')
document.add_paragraph('The project includes the required technical documentation and deployment evidence within the repository and supporting files. The final written report is provided as a Word document and can be shared as a PDF if required. The report remains concise, professional, and aligned with the assignment brief while preserving the technical depth needed for assessment.')
document.add_paragraph('Video demo link: Add video link here')
document.add_paragraph('Repository link: https://github.com/sanjaybet/mlops_assignment01')
document.add_page_break()

add_section_heading(document, '11. Deliverables checklist')
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
    'Video demo link (still to be added)',
]:
    document.add_paragraph(f'• {item}')

document.add_paragraph('')
document.add_paragraph('Conclusion: The project was implemented and validated as a complete MLOps pipeline for heart disease prediction. It covers data acquisition, cleansing, experimentation, deployment, automation, and reporting in a way that aligns with the assignment specification and production-readiness expectations.')

output_path = '2025ae05368_mlops_assignment1_report.docx'
if __name__ == '__main__':
    document.save(output_path)
    print(f'Created {output_path}')
