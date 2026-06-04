"""
Combine Harry's manually corrected warps (in SWC template space)
and Viktor's automatically generated warps (in Waxholm template space) into a single template.
This will be used as a registration target for the original Waxholm template.
The transformations will be applied to the original waxholm annotations.
"""

import nibabel as nib
import numpy as np

# ------------------------------------------------------------------
# 1. LOAD TEMPLATES
# ------------------------------------------------------------------
harrys_template = nib.load("/home/viktor/brainglobe_workingdir/swc_female_rat/harrys_warps/warped.nii.gz")
viktors_template = nib.load("/home/viktor/brainglobe_workingdir/swc_female_rat/W2T_warped.nii.gz")

harrys_template_data = harrys_template.get_fdata()  # voxel intensities as numpy array
viktors_template_data = viktors_template.get_fdata()

viktors_affine = viktors_template.affine
harrys_affine = harrys_template.affine
print("Viktors affine: ", "\n", "\n", "\n", viktors_affine)
print("Harry's affine: ", "\n", "\n", "\n", harrys_affine)

viktors_template_header = viktors_template.header
harrys_template_header = harrys_template.header
print("Viktors header: ", "\n", "\n", "\n", viktors_template_header)
print("Harry's header: ", "\n", "\n", "\n", harrys_template_header)

print("Loaded volumes:", harrys_template_data.shape, viktors_template_data.shape)

# ------------------------------------------------------------------
# 2. APPLY VIKTOR'S HEADER TO HARRY'S DATA
# ------------------------------------------------------------------
# Same voxel array; replace Harry's spatial metadata with Viktor's (affine + header).
harrys_template_with_viktors_header = nib.Nifti1Image(
    harrys_template_data,
    viktors_affine,
    header=viktors_template_header.copy(),
)

# harrys_template_with_viktors_header_path = (
#     "/home/viktor/brainglobe_workingdir/swc_female_rat/harrys_warps/warped_viktor_header.nii.gz"
# )
# nib.save(harrys_template_with_viktors_header, harrys_template_with_viktors_header_path)
# print("Saved:", harrys_template_with_viktors_header_path)

# ------------------------------------------------------------------
# 3. COMBINE ALONG AXIS 0 (length 1030)
# ------------------------------------------------------------------
harrys_for_combine = harrys_template_with_viktors_header.get_fdata()
viktors_for_combine = viktors_template_data

assert harrys_for_combine.shape == viktors_for_combine.shape == (1030, 500, 660)

split_i = 715  # Harry: 0..714, Viktor: 715..1029

combined_template_data = np.empty_like(harrys_for_combine)
combined_template_data[0:split_i, :, :] = harrys_for_combine[0:split_i, :, :]
combined_template_data[split_i:, :, :] = viktors_for_combine[split_i:, :, :]

combined_template = nib.Nifti1Image(
    combined_template_data,
    viktors_affine,
    header=viktors_template_header.copy(),
)

# ------------------------------------------------------------------
# 4. SAVE
# ------------------------------------------------------------------
nib.save(combined_template, "/home/viktor/brainglobe_workingdir/swc_female_rat/harrys_warps/warped_combined.nii.gz")
print("Saved:", "/home/viktor/brainglobe_workingdir/swc_female_rat/harrys_warps/warped_combined.nii.gz")
