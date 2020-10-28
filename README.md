# Introduction
This is a PoC that shows how it is possible to download a DRM protected video from a website.

This example expect a wesite that provides video-courses and expose the following API:
* GET /trainer-uuid
  * Parameters: None
  * Description: Return a list of courses made by the trainer with the UUID specified
* GET /api/course
  * Parameters:
    * course_id: UUID for the specified course
  * Description: Return the list of lessons for the course with the specified UUID
* GET /api/video
  * Parameters
    * lesson_id: UUID for the specified video
  * Description: Return information about the video with the specified UUID. This includes for example the master playlist, subtitles etc.

# downloader.py

A list of trainers is retrieved from the file trainers.txt and the script iterate over it, over the courses belonging to a specific trainer and finally over the video belonging to a specific course.

Data returned from /api/video is processed to get the variant playlist. From this playlist the playlist of segments with the highest average bitrate is choosen, which is then downloaded.

The segment's playlist contains also the URI for the key to be used to decrypt the video and the IV, assuming the segments are encrypted with AES.

Key and IV are seved in the same folder of the segments.

# decrypt.py

This script uses the AES key and IV present inside the lesson's folder to decrypt the segments and to merge them in a single file.

# package.py

This script is moving all the files inside a specific folder, preparing them for the final storage.

A round with ffmpeg is done in order to ensure the container is mp4.
