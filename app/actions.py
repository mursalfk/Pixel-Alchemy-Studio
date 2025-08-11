import os
from tkinter import filedialog, messagebox
from utils.image_io import list_images_in_folder, load_bgr, save_bgr
from processing.pipeline import cyberpunkify_pipeline

# Small actions to keep app.py lean

def do_open_image(app):
    path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp")],
    )
    if not path:
        return
    app.state.current_path = path
    try:
        img = load_bgr(path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load image:\n{e}")
        return
    app.state.original = img
    app.refresh()


def do_choose_folder(app):
    folder = filedialog.askdirectory(title="Choose a folder with images")
    if not folder:
        return
    app.state.current_folder = folder
    app.left.populate_thumbs(folder)


def do_save_image(app):
    if app.state.processed is None:
        messagebox.showinfo("Info", "No processed image to save.")
        return
    base = (
        os.path.splitext(os.path.basename(app.state.current_path))[0] + "_cyberpunk.png"
        if app.state.current_path
        else "output_cyberpunk.png"
    )
    path = filedialog.asksaveasfilename(
        defaultextension=".png",
        initialfile=base,
        filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("All", "*.*")],
    )
    if not path:
        return
    try:
        save_bgr(path, app.state.processed)
        messagebox.showinfo("Saved", f"Saved:\n{path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save image:\n{e}")


def do_process_batch(app):
    mode = app.state.pick_mode
    targets = []

    if mode == "folder":
        if not app.state.current_folder:
            ttk.messagebox.showinfo("Info", "Choose a folder first.")
            return
        targets = list_images_in_folder(app.state.current_folder)
    elif mode == "multi":
        if not app.state.multiselect:
            ttk.messagebox.showinfo("Info", "Select images from the list.")
            return
        targets = list(app.state.multiselect)
    else:
        if not app.state.current_path:
            ttk.messagebox.showinfo("Info", "Open or click an image first.")
            return
        targets = [app.state.current_path]

    outdir = filedialog.askdirectory(title="Choose an output folder")
    if not outdir:
        return

    params = app.params()
    ok, fail = 0, 0
    total = len(targets)

    # progress start
    if hasattr(app, "right"):
        app.right.set_progress(0, total, "Batch 0/{}".format(total))
        app.right.progress_start("Batch...")  # indeterminate while we warm up
        app.update_idletasks()

    try:
        # switch to determinate after first item
        for i, path in enumerate(targets, start=1):
            try:
                img = load_bgr(path)
                pipeline = get_pipeline(app.state.current_theme)
                out = pipeline(img, **params)
                base = os.path.splitext(os.path.basename(path))[0] + "_cyberpunk.png"
                save_bgr(os.path.join(outdir, base), out)
                ok += 1
            except Exception:
                fail += 1

            if hasattr(app, "right"):
                if i == 1:
                    # stop spinner, show determinate
                    app.right.progress_stop()
                app.right.set_progress(i, total, "Batch {}/{}".format(i, total))
                app.update_idletasks()
    finally:
        if hasattr(app, "right"):
            app.right.progress_stop("Done")

    messagebox.showinfo("Batch Done", f"Processed: {ok}\nFailed: {fail}\nSaved to: {outdir}")
