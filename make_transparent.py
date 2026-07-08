import os
import numpy as np
from PIL import Image, ImageSequence


INPUT_GIF = "target.gif"
OUTPUT_GIF = "target_transparent.gif"

# Mode:
# "corner" = warna background diambil dari pojok kiri atas
# "manual" = warna background ditentukan sendiri
KEY_MODE = "corner"

# Kalau background green screen, aktifkan manual:
# KEY_MODE = "manual"
# KEY_COLOR = (0, 255, 0)
KEY_COLOR = (0, 255, 0)

# Toleransi hapus background
# Kalau background masih nyisa, naikkan
# Kalau jas ikut bolong, turunkan
TOLERANCE = 40

# Penting:
# False = mempertahankan posisi asli animasi, jadi efek jalan tetap ada
# True = crop area animasi secara global, bukan per frame
TRIM_GLOBAL_CANVAS = False


def get_background_color(frame):
    frame = frame.convert("RGBA")
    pixels = frame.load()
    width, height = frame.size

    if KEY_MODE == "manual":
        return KEY_COLOR

    corners = [
        pixels[0, 0][:3],
        pixels[width - 1, 0][:3],
        pixels[0, height - 1][:3],
        pixels[width - 1, height - 1][:3],
    ]

    avg = tuple(
        int(sum(color[i] for color in corners) / len(corners))
        for i in range(3)
    )

    return avg


def remove_background(frame):
    frame = frame.convert("RGBA")
    data = np.array(frame)

    bg_color = np.array(get_background_color(frame))

    rgb = data[:, :, :3]
    alpha = data[:, :, 3]

    distance = np.sqrt(np.sum((rgb - bg_color) ** 2, axis=2))

    mask = distance <= TOLERANCE

    data[:, :, 3] = np.where(mask, 0, alpha)

    return Image.fromarray(data, "RGBA")


def get_global_bbox(frames):
    final_bbox = None

    for frame in frames:
        bbox = frame.getchannel("A").getbbox()

        if bbox is None:
            continue

        if final_bbox is None:
            final_bbox = bbox
        else:
            left = min(final_bbox[0], bbox[0])
            top = min(final_bbox[1], bbox[1])
            right = max(final_bbox[2], bbox[2])
            bottom = max(final_bbox[3], bbox[3])

            final_bbox = (left, top, right, bottom)

    return final_bbox


def crop_global(frames):
    bbox = get_global_bbox(frames)

    if bbox is None:
        return frames

    return [frame.crop(bbox) for frame in frames]


def save_transparent_gif(frames, output_path, durations):
    if not frames:
        print("Tidak ada frame yang diproses.")
        return

    width, height = frames[0].size

    palette_source = Image.new(
        "RGBA",
        (width * len(frames), height),
        (255, 255, 255, 0)
    )

    for i, frame in enumerate(frames):
        palette_source.paste(frame, (i * width, 0), frame)

    rgb_palette_source = Image.new(
        "RGB",
        palette_source.size,
        (255, 255, 255)
    )

    rgb_palette_source.paste(
        palette_source,
        mask=palette_source.getchannel("A")
    )

    quantized_palette_source = rgb_palette_source.quantize(
        colors=255,
        method=Image.MEDIANCUT,
        dither=Image.Dither.NONE
    )

    base_palette = quantized_palette_source.getpalette()[:255 * 3]

    final_palette = [0, 0, 0] + base_palette
    final_palette += [0] * (768 - len(final_palette))

    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(
        base_palette + [0] * (768 - len(base_palette))
    )

    paletted_frames = []

    for frame in frames:
        rgb_frame = Image.new("RGB", frame.size, (255, 255, 255))
        rgb_frame.paste(frame, mask=frame.getchannel("A"))

        q_frame = rgb_frame.quantize(
            palette=palette_image,
            dither=Image.Dither.NONE
        )

        color_data = np.array(q_frame, dtype=np.uint16)
        alpha_data = np.array(frame.getchannel("A"))

        final_data = color_data + 1
        final_data[alpha_data == 0] = 0

        p_frame = Image.fromarray(final_data.astype("uint8"), "P")
        p_frame.putpalette(final_palette)

        p_frame.info["transparency"] = 0
        p_frame.info["disposal"] = 2

        paletted_frames.append(p_frame)

    first_duration = durations[0] if durations else 120

    paletted_frames[0].save(
        output_path,
        save_all=True,
        append_images=paletted_frames[1:],
        duration=durations if durations else first_duration,
        loop=0,
        transparency=0,
        disposal=2,
        optimize=False
    )


def main():
    if not os.path.exists(INPUT_GIF):
        print(f"File tidak ditemukan: {INPUT_GIF}")
        return

    gif = Image.open(INPUT_GIF)

    fixed_frames = []
    durations = []

    for frame in ImageSequence.Iterator(gif):
        frame_rgba = frame.convert("RGBA")

        clean = remove_background(frame_rgba)

        fixed_frames.append(clean)
        durations.append(frame.info.get(
            "duration", gif.info.get("duration", 120)))

    if TRIM_GLOBAL_CANVAS:
        fixed_frames = crop_global(fixed_frames)

    save_transparent_gif(
        fixed_frames,
        OUTPUT_GIF,
        durations
    )

    print(f"Selesai: {OUTPUT_GIF}")


if __name__ == "__main__":
    main()
