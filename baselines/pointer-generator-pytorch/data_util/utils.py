#Content of this file is copied from https://github.com/abisee/pointer-generator/blob/master/
import config
import os
import sys
sys.path.append(config.pyrouge_path)
import pyrouge
import logging
import tensorflow as tf

def print_results(article, abstract, decoded_output):
  print ("")
  print('ARTICLE:  %s', article)
  print('REFERENCE SUMMARY: %s', abstract)
  print('GENERATED SUMMARY: %s', decoded_output)
  print( "")


def make_html_safe(s):
  s.replace("<", "&lt;")
  s.replace(">", "&gt;")
  return s


def rouge_eval(ref_dir, dec_dir, n_bytes):
  r = pyrouge.Rouge155(n_bytes=n_bytes)
  logging.getLogger('global').setLevel(logging.WARNING) # silence pyrouge logging
  # return r.evaluate_folder_macro_average(dec_dir, ref_dir)
  return r.evaluate_folder(dec_dir, ref_dir)


def rouge_log(results_dict, dir_to_write):
  results_file = os.path.join(dir_to_write, "ROUGE_results.txt")
  with open(results_file, 'w') as f:
    log_str = ""
    for x in ["1","2","l"]:
      log_str += "\nROUGE-%s:\n" % x
      for y in ["f_score", "recall", "precision"]:
        key = "rouge_%s_%s" % (x,y)
        key_cb = key + "_cb"
        key_ce = key + "_ce"
        val = results_dict[key]
        val_cb = results_dict[key_cb]
        val_ce = results_dict[key_ce]
        log_str += "%s: %.4f with confidence interval (%.4f, %.4f)\n" % (key, val, val_cb, val_ce)
    print(log_str)
    f.write(log_str)


def calc_running_avg_loss(loss, running_avg_loss, summary_writer, step, decay=0.99):
  if running_avg_loss == 0:  # on the first iteration just take the loss
    running_avg_loss = loss
  else:
    running_avg_loss = running_avg_loss * decay + (1 - decay) * loss
  running_avg_loss = min(running_avg_loss, 12)  # clip
  loss_sum = tf.Summary()
  tag_name = 'running_avg_loss/decay=%f' % (decay)
  loss_sum.value.add(tag=tag_name, simple_value=running_avg_loss)
  summary_writer.add_summary(loss_sum, step)
  return running_avg_loss


def write_for_rouge(reference_sents, decoded_words, ex_index,
                    _rouge_ref_dir, _rouge_dec_dir):
  decoded_sents = []
  while len(decoded_words) > 0:
    try:
      fst_period_idx = decoded_words.index(".")
    except ValueError:
      fst_period_idx = len(decoded_words)
    sent = decoded_words[:fst_period_idx + 1]
    decoded_words = decoded_words[fst_period_idx + 1:]
    decoded_sents.append(' '.join([x if isinstance(x, str) else x.decode('utf-8') for x in sent]))

  # pyrouge calls a perl script that puts the data into HTML files.
  # Therefore we need to make our output HTML safe.
  decoded_sents = [make_html_safe(w) for w in decoded_sents]
  reference_sents = [make_html_safe(w) for w in reference_sents]

  ref_file = os.path.join(_rouge_ref_dir, "%06d_reference.txt" % ex_index)
  decoded_file = os.path.join(_rouge_dec_dir, "%06d_decoded.txt" % ex_index)

  with open(ref_file, "w") as f:
    for idx, sent in enumerate(reference_sents):
      f.write(sent) if idx == len(reference_sents) - 1 else f.write(sent + "\n")
  with open(decoded_file, "w") as f:
    for idx, sent in enumerate(decoded_sents):
      f.write(sent) if idx == len(decoded_sents) - 1 else f.write(sent + "\n")

  #print("Wrote example %i to file" % ex_index)
