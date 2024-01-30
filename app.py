import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Import ttk for Progressbar
import requests
import threading

# Create the main window
window = tk.Tk()
window.title("Video Downloader")

# Create a label and entry for the URL
url_label = tk.Label(window, text="Enter URL:")
url_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
url_entry = tk.Entry(window, width=40)
url_entry.grid(row=0, column=1, padx=10, pady=10)

# Create a progress bar and label
progress_label = tk.Label(window, text="Progress:")
progress_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(window, variable=progress_var, maximum=100)
progress_bar.grid(row=1, column=1, padx=10, pady=10, sticky="we")

# Create a label to display the number of videos downloaded
num_videos_label = tk.Label(window, text="Number of videos downloaded: 0")
num_videos_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)


# Function to update the progress bar
def update_progress(progress):
    progress_var.set(progress)


# Function to download the video
def download_video():
    global download_thread
    url = url_entry.get()
    if not url:
        messagebox.showerror("Error", "Please enter a valid URL")
        return

    # Make a GET request in a separate thread
    download_thread = threading.Thread(target=download_thread_function, args=(url,))
    download_thread.start()


# Function to stop the download
def stop_download():
    global download_thread
    if download_thread.is_alive():
        download_thread.join()
        messagebox.showinfo("Info", "Download stopped")


# Function to download the video in a separate thread
def download_thread_function(url):
    try:
        # response = requests.get(url, stream=True)
        response = requests.post(
            url="http://localhost:5050/download/mp4",
            json={
                "video_url": url,
            },
            headers={
                "Content-Type": "application/json",
            },
            stream=True,
        )
        response.raise_for_status()  # Check for any HTTP errors
        content_length = response.headers.get('content-length')
        if content_length is None:
            messagebox.showerror("Error", "Content length not provided by the server")
            return
        content_length = int(content_length)
        chunk_size = 1024
        downloaded = 0
        num_videos = 0

        with open(f"video{num_videos+1}.mp4", "wb") as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
                downloaded += len(data)
                progress = int((downloaded / content_length) * 100)
                window.after(100, update_progress, progress)  # Update progress bar
                if not download_thread.is_alive():
                    return
        num_videos += 1
        num_videos_label.config(text=f"Number of videos downloaded: {num_videos}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


# Create a button to start the download
download_button = tk.Button(window, text="Download", command=download_video)
download_button.grid(row=3, column=0, padx=10, pady=10)

# Create a button to stop the download
stop_button = tk.Button(window, text="Stop Downloading", command=stop_download)
stop_button.grid(row=3, column=1, padx=10, pady=10)

# Run the main loop
window.mainloop()
