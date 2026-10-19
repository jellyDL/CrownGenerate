python step2_render_heatmap.py 00004f28-f49f-58f8-8ef8-8504fdcbca6f --clim 0.8 --jaw-reduction 0.94
python step2_render_heatmap.py 00846fbb-7b3f-557a-ba1e-cc10747383de --clim 0.8 --jaw-reduction 0.93
python step2_render_heatmap.py 02b425f7-d65e-5813-ad69-11837a2977bf --clim 1.0 --jaw-reduction 0.95
python step2_render_heatmap.py 058268c5-dc9c-50b0-9c49-e2fb867dd41e --clim 0.8 --jaw-reduction 0.94
python step3_merge_imgs.py --colorbar-position 3100 1940 --clim 0 0.6  \
  --cases 00004f28-f49f-58f8-8ef8-8504fdcbca6f \
          00846fbb-7b3f-557a-ba1e-cc10747383de \
          02b425f7-d65e-5813-ad69-11837a2977bf \
          058268c5-dc9c-50b0-9c49-e2fb867dd41e
