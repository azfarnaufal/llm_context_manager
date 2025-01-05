import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from main import ConversationManager

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'txt'}

if not os.path.exists(UPLOAD_FOLDER):
	os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		# Check if a file was uploaded
		if 'file' not in request.files:
			flash('No file selected')
			return redirect(request.url)
		
		file = request.files['file']
		if file.filename == '':
			flash('No file selected')
			return redirect(request.url)
		
		if file and allowed_file(file.filename):
			# Secure the filename and save the file
			filename = secure_filename(file.filename)
			filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			file.save(filepath)
			
			try:
				# Process the file using ConversationManager
				manager = ConversationManager()
				final_summary = manager.process_conversation(open(filepath, 'r').read())
				
				# Save the results
				summary_filename = f"summary_{filename}"
				summary_filepath = os.path.join(app.config['UPLOAD_FOLDER'], summary_filename)
				with open(summary_filepath, 'w') as f:
					f.write(final_summary)
				
				# Save state
				state_filename = f"state_{filename.replace('.txt', '.json')}"
				state_filepath = os.path.join(app.config['UPLOAD_FOLDER'], state_filename)
				manager.save_state(state_filepath)
				
				return render_template('result.html', 
									 summary=final_summary,
									 summary_file=summary_filename,
									 state_file=state_filename)
			
			except Exception as e:
				flash(f'Error processing file: {str(e)}')
				return redirect(request.url)
		else:
			flash('Only .txt files are allowed')
			return redirect(request.url)
	
	return render_template('upload.html')

@app.route('/download/<filename>')
def download_file(filename):
	try:
		return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename),
						as_attachment=True)
	except Exception as e:
		flash(f'Error downloading file: {str(e)}')
		return redirect(url_for('upload_file'))

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)