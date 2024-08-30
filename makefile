run:
	poetry run python hakai_qc_app/app.py

clean:
	rm logs/dashboard.log
	rm temp/*
