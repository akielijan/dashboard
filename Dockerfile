FROM python:3.7
USER root
WORKDIR /app
RUN git clone https://github.com/akielijan/dashboard.git /app
RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt
RUN sed -i 's/app.run_server(debug=True)/app.run_server(debug=False, host="0.0.0.0", port=8050)/g' /app/dashboard.py
EXPOSE 8050
CMD ["python", "/app/dashboard.py"]
