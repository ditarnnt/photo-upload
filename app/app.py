from flask import Flask, jsonify, request, render_template
import ibm_boto3
from ibm_botocore.client import Config
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

end_point_url_public = "s3.ap.cloud-object-storage.appdomain.cloud"
COS_ENDPOINT = "https://" + end_point_url_public
COS_API_KEY_ID = os.getenv("COS_API_KEY_ID")
COS_INSTANCE_CRN = os.getenv("COS_INSTANCE_CRN")
bucket_name = os.getenv("bucket_name")

print(end_point_url_public)
print(COS_API_KEY_ID)
print(COS_ENDPOINT)
print(COS_INSTANCE_CRN)
print(bucket_name)

app = Flask(__name__, template_folder="templates")
app.secret_key = "UPLOAD123"
CORS(app)

base_path = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(base_path, "user_files")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def index():
    return render_template("upload_photo.html")


@app.route("/mock_upload")
def show():
    return render_template("mock_upload.html")


@app.route("/generate-presigned-url", methods=["POST", "GET"])
def generate_presigned_url():
    file_photo = request.files["file"]
    print(file_photo)
    filename = secure_filename(file_photo.filename)
    print(filename)
    # Save the file to the uploads folder
    complete_file_loc = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file_photo.save(complete_file_loc)

    print(complete_file_loc)

    if not file_photo:
        app.logger.error("File name not provided or is empty.")
        return jsonify({"error": "File name not provided or is empty"}), 400

    print("otw connection")
    # Initialize IBM COS Resource
    cos_client = ibm_boto3.client(
        "s3",
        ibm_api_key_id=COS_API_KEY_ID,
        ibm_service_instance_id=COS_INSTANCE_CRN,
        config=Config(signature_version="oauth"),
        endpoint_url=COS_ENDPOINT,
    )

    if cos_client._request_signer._credentials is None:
        print("Credentials are not loaded correctly.")
    else:
        if (
            not hasattr(cos_client._request_signer._credentials, "token")
            or cos_client._request_signer._credentials.token is None
        ):
            print("Token is not available in the credentials.")

    # Upload Photo
    file_id = filename
    cos = cos_client.upload_file(
        Filename=complete_file_loc, Bucket=bucket_name, Key=file_id
    )
    print(f"upload file to {cos}")
    cos_endpoint = (
        f"https://{bucket_name}.s3.ap.cloud-object-storage.appdomain.cloud/{file_id}"
    )
    print(cos_endpoint)

    # Generate presigned URL
    # presigned_url = cos.generate_presigned_url('put_object',
    #                                            Params={'Bucket': bucket_name,
    #                                                    'Key': file_name},
    #                                            ExpiresIn=3600)
    # print(presigned_url)
    # return jsonify({'url': presigned_url})
    # except Exception as e:
    # app.logger.error(f"Error generating presigned URL: {str(e)}")
    # return jsonify({'error': str(e)}), 500
    return jsonify({"url": cos_endpoint})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
