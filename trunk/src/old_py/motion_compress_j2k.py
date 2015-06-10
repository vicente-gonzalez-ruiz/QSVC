


'''
check_call("echo AQUI", shell=True) #  !!!!
raw_input("\nFIN\nPress ENTER to continue ...") # !
sys.exit("\nSTOP !\n")

        check_call("trace demux " + str(COMPONENTS * BYTES_PER_COMPONENT) + " " + str(i * BYTES_PER_COMPONENT) + " " + str(BYTES_PER_COMPONENT)
                   + " < " + file
                   + " | /usr/bin/split --numeric-suffixes --suffix-length=4 "
                   + "--bytes=" + str(bytes_compF) + " - " + file + "_comp" + str(i) + "_", # .rawl aquí!
                   shell=True)



        check_call("echo -e \"trace demux " + str(COMPONENTS * BYTES_PER_COMPONENT) + " " + str(i * BYTES_PER_COMPONENT) + " " + str(BYTES_PER_COMPONENT)
                   + " < " + file
                   + " > " + file + "_comp" + str(i) + "\"", shell=True)
        raw_input("\n i=" + str(i) + "Press ENTER to continue ...")



kdu_compress -i motion_residue_1_0001.raw*4@1584 -o out.jpx Creversible=yes Sdims='{'22,18'}' -jpx_layers 4 Clayers=6 Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes

kdu_compress -i motion_residue_1_0001.raw*4@1584 -o out.jpx Creversible=yes Sdims='{'22,18'}' Clayers=6 Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes

kdu_compress -i motion_residue_1_0001.raw*4@1584 -o out.jpx Creversible=yes Sdims='{'22,18'}' Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes

kdu_compress -i motion_residue_1_0001.raw*4@304128 -o out.jpx Creversible=yes Sdims='{'22,18'}' Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes

kdu_compress -i motion_residue_1_0001.raw*4@396  -o out.jpx Creversible=yes Sdims='{'22,18'}' Mcomponents=4 Msigned=no Mprecision=8 Sprecision=8,8,8,8 Ssigned=yes,yes,yes,yes
'''
