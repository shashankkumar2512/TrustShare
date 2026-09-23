import { sharedWithMeAPI } from '../../../utils/api';

export async function fetchSharedFiles() {
  const response = await sharedWithMeAPI.list();
  return response.data;
}

export async function downloadSharedFile(file) {
  const response = await sharedWithMeAPI.download(file.file_id);
  const url = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = file.name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function viewSharedFile(file) {
  const newTab = window.open('', '_blank');

  try {
    const response = await sharedWithMeAPI.view(file.file_id);

    const contentType =
      response.headers['content-type'] ||
      file.mimetype ||
      'application/octet-stream';

    const blob = new Blob([response.data], { type: contentType });
    const url = URL.createObjectURL(blob);

    if (newTab) {
      newTab.location.href = url;
    }

    setTimeout(() => URL.revokeObjectURL(url), 30000);
  } catch (err) {
    if (newTab) newTab.close();
    throw err;
  }
}