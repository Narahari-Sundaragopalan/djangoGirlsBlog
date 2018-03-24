from .models import Post
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from .forms import PostForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from watson_developer_cloud import ToneAnalyzerV3
from watson_developer_cloud import LanguageTranslatorV2 as LanguageTranslator
import json

# Create your views here.


def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    # Using Watson's Tone Analyzer
    tone_analyzer = ToneAnalyzerV3(
        username= "02582eca-2c78-4f03-bb86-c1d5912d4741",
        password= "cp6yGjikDWP1",
        version="2016-05-19"
    )
    # Using Watson's Language Translator
    language_translator = LanguageTranslator(
        username= "cfc9e2aa-b6e6-4cce-9bbb-2c3655669302",
        password= "LVmtzRmQFzt5"
    )
    for post in posts:
        post_text = post.text
        tone_object = json.dumps(tone_analyzer.tone(tone_input=post_text,
                                        content_type="text/plain"), indent=2)
        post.tone_json_object = json.loads(tone_object)
        post.anger_score = post.tone_json_object['document_tone']['tone_categories'][0]['tones'][0]['score']
        post.disgust_score = post.tone_json_object['document_tone']['tone_categories'][0]['tones'][1]['score']
        post.fear_score = post.tone_json_object['document_tone']['tone_categories'][0]['tones'][2]['score']
        post.joy_score = post.tone_json_object['document_tone']['tone_categories'][0]['tones'][3]['score']
        post.sad_score = post.tone_json_object['document_tone']['tone_categories'][0]['tones'][4]['score']

        translation = language_translator.translate(
            text=post.text,
            source='en',
            target='es'
            )
        translation_object = json.dumps(translation, indent=2, ensure_ascii=False)
        post.translation_json_object = json.loads(translation_object)
        post.translations = post.translation_json_object['translations']
        post.word_count = post.translation_json_object['word_count']
        post.character_count = post.translation_json_object['character_count']

    return render(request, 'blog/post_list.html', {'posts': posts})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})


@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            #post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            #post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def post_draft_list(request):
    posts = Post.objects.filter(published_date__isnull=True).order_by('created_date')
    return render(request, 'blog/post_draft_list.html', {'posts': posts})


@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return redirect('post_detail', pk=pk)


@login_required
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect('post_list')
