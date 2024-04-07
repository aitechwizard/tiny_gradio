import os
import io
import sys
import gradio as gr
import tinify
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('TINIFY_API_KEY')
print('api_key', api_key)
if api_key == '':
    print('No API key')
    sys.exit(1)

tinify.key = api_key

# 需要压缩的图片列表
image_path_list = []

# 允许压缩的图片格式
valid_ext = ['.png', '.jpg', '.jpeg']

valid_cp_type = ['tiny', 'tiny+webp']


def upload_files(files):
    file_paths = []
    for file in files:
        file_paths.append(file.name)
        image_path_list.append(file)
    return file_paths


# tiny 图片压缩
def tiny_compress_core(input_file, output_file, img_width):
    source = tinify.Source.from_file(input_file)
    if img_width != -1:
        resized = source.resize(method="scale", width=img_width)
        resized.to_file(output_file)
    else:
        source.to_file(output_file)


def tiny_compress_data(input_file, img_width):
    source = tinify.Source.from_file(input_file)
    if img_width != -1:
        resized = source.resize(method="scale", width=img_width)
        return resized.to_buffer()
    else:
        return source.to_buffer()


def tiny_compress(output_dir, img_path_list):
    for path in img_path_list:
        image_name, ext = os.path.splitext(os.path.basename(path))
        if ext not in valid_ext:
            continue

        image_output_path = output_dir.rstrip('/') + '/' + image_name + '_compress' + ext
        print('compress info:', path, image_output_path)
        tiny_compress_core(path, image_output_path, -1)
    print('tiny compress success!')


def tiny_webp_compress(output_dir, img_path_list):
    for path in img_path_list:
        image_name, ext = os.path.splitext(os.path.basename(path))
        if ext not in valid_ext:
            continue

        tiny_data = tiny_compress_data(path, -1)
        image_bytes = io.BytesIO(tiny_data)

        im = Image.open(image_bytes)
        image_output_path = output_dir.rstrip('/') + '/' + image_name + '_compress' + '.webp'

        print('compress info:', path, image_output_path)
        im.save(image_output_path, 'WebP', quality=80)

    print('tiny webp compress success!')


def compress(single_file, output_dir, compress_type, fu):
    if single_file != '':
        if single_file not in image_path_list:
            image_path_list.append(single_file)

    if compress_type not in valid_cp_type:
        return 'Invalid compress type'

    if output_dir == '':
        return 'Invalid output directory'

    if not os.path.exists(output_dir):
        return 'Output directory not exists'

    print('output dir:', output_dir)
    print('image_path_list:', image_path_list)
    if compress_type == 'tiny':
        tiny_compress(output_dir, image_path_list)
        return 'tiny compress success!'

    if compress_type == 'tiny+webp':
        tiny_webp_compress(output_dir, image_path_list)
        return 'tiny+webp compress success!'

    return 'None'


with gr.Blocks() as app:
    # 文件选择列表
    file_select_gr = gr.File(label="待压缩图片")
    # 图片保存路径
    output_dir_gr = gr.Textbox(lines=1, label='图片保存路径（必选）', placeholder='压缩后的图片保存路径')
    # 压缩方式选择
    compress_type_gr = gr.Dropdown(valid_cp_type, value='tiny+webp', label='compress type')
    # 图片上传按钮(多张图片)
    file_upload_btn_gr = gr.UploadButton("Upload Multi Image", file_types=["image"], file_count="multiple")
    file_upload_btn_gr.upload(upload_files, file_upload_btn_gr, file_select_gr)

    gr.Interface(
        fn=compress,
        inputs=[file_select_gr, output_dir_gr, compress_type_gr, file_upload_btn_gr],
        outputs=["text"],
        submit_btn='Compress',
        allow_flagging='never'
    )

if __name__ == '__main__':
    app.launch()
